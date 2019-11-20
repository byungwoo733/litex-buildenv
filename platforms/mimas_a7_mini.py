from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [
    ("user_led", 0, Pins("K12"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("K13"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("R10"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("R13"), IOStandard("LVCMOS33")),
    ("user_led", 4, Pins("T13"), IOStandard("LVCMOS33")),
    ("user_led", 5, Pins("R12"), IOStandard("LVCMOS33")),
    ("user_led", 6, Pins("T12"), IOStandard("LVCMOS33")),
    ("user_led", 7, Pins("R11"), IOStandard("LVCMOS33")),

    ("user_btn", 0, Pins("F5"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("J4"), IOStandard("LVCMOS33")),
    ("user_btn", 2, Pins("M6"), IOStandard("LVCMOS33")),
    ("user_btn", 3, Pins("N6"), IOStandard("LVCMOS33")),

    ("clk100", 0, Pins("N11"), IOStandard("LVCMOS33")),
    
    ("cpu_reset", 0, Pins("N6"), IOStandard("LVCMOS33")),

    # J13 - QSPI_DQ0 - MOSI
    # J14 - QSPI_DQ1 - MISO
    # K15 - QSPI_DQ2 - ~WP
    # K16 - QSPI_DQ3 - ~HOLD
    # L12 - QSPI_CS  - ~CS
    # E8 - CCLK
    ("spiflash_4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("L12")),
        Subsignal("dq", Pins("J13", "J14", "K15", "K16")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash_1x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("L12")),
        Subsignal("mosi", Pins("J13")),
        Subsignal("miso", Pins("J14")),
        Subsignal("wp", Pins("K15")),
        Subsignal("hold", Pins("K16")),
        IOStandard("LVCMOS33")
    ),

    ("serial", 0,
        Subsignal("tx", Pins("N16")),
        Subsignal("rx", Pins("M16")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "C7 B1 C1 D6 A3 C6 A2 B6",
            "B2 B5 E2 C2 C3 B4"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("D3 E3 D1"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("D4"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("C4"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("B7"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("E5 J5"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "G2  F3  H4   G5  G1  F4  H5  G4",
            "H2  H1  K1  J1  L3  L2  K3  K2"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("F2 J3"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("E1 H3"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("A5"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("A4"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("D5"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("A7"), IOStandard("SSTL15")),
        Subsignal("cs_n", Pins("E6"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("K5"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),

]


class Platform(XilinxPlatform):
    name = "mimas_a7_mini"
    default_clk_name = "clk100"
    default_clk_period = 10.0

    # From https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf
    # 17,536,096 bits == 2192012 bytes == 0x21728c -- Therefore 0x220000
    gateware_size = 0x220000

    # Spansion S25FL256S (ID 0x00190201)
    # FIXME: Create a "spi flash module" object in the same way we have SDRAM
    # module objects.
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((128/8)*1024*1024) # 256Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000
    spiflash_model = "n25q128"

    def __init__(self, toolchain="vivado", programmer="openocd"):
        XilinxPlatform.__init__(self, "xc7a35t-ftg256-1", _io,
                                toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 35]")


    def create_programmer(self):
        if self.programmer == "openocd":
            proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
            return OpenOCD(config="board/numato_mimas_a7_mini.cfg", flash_proxy_basename=proxy)
        elif self.programmer == "xc3sprog":
            return XC3SProg("nexys4")
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4") # FIXME: Spansion S25FL256S
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))
