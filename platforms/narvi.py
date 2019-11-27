from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer

_io = [
    ("user_led", 0, Pins("G13"), IOStandard("LVCMOS33")),

    ("clk100", 0, Pins("D14"), IOStandard("LVCMOS33")),

    ("cpu_reset", 0, Pins("T14"), IOStandard("LVCMOS33")),

    # K17 - QSPI_DQ0 - MOSI
    # K18 - QSPI_DQ1 - MISO
    # L14 - QSPI_DQ2 - ~WP
    # M15 - QSPI_DQ3 - ~HOLD
    # M13 - QSPI_CS  - ~CS
    # C8 - CCLK
    ("spiflash_4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("M13")),
        Subsignal("dq", Pins("K17", "K18", "L14", "M15")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash_1x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("M13")),
        Subsignal("mosi", Pins("K17")),
        Subsignal("miso", Pins("K18")),
        Subsignal("wp", Pins("L14")),
        Subsignal("hold", Pins("M15")),
        IOStandard("LVCMOS33")
    ),

    ("serial", 0,
        Subsignal("tx", Pins("N13")),
        Subsignal("rx", Pins("L13")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "P5 P6 T3 R4 V4 V5 V2 V3",
            "U2 U3 U1 T1 T2 R3"),
            IOStandard("SSTL15")),
        Subsignal("ba", Pins("T6 V6 V7"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("T5"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("R7"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("R6"), IOStandard("SSTL15")),
        Subsignal("dm", Pins("K4 M3"), IOStandard("SSTL15")),
        Subsignal("dq", Pins(
            "L4  K3  K2  K6  L6  L5  M4  M6",
            "M2  M1  N1  N5  N4  P2  P1  R2"),
            IOStandard("SSTL15"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("K1 N3"), IOStandard("DIFF_SSTL15")),
        Subsignal("dqs_n", Pins("L1 N2"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_p", Pins("R5"), IOStandard("DIFF_SSTL15")),
        Subsignal("clk_n", Pins("T4"), IOStandard("DIFF_SSTL15")),
        Subsignal("cke", Pins("U6"), IOStandard("SSTL15")),
        Subsignal("odt", Pins("P7"), IOStandard("SSTL15")),
        Subsignal("cs_n", Pins("U7"), IOStandard("SSTL15")),
        Subsignal("reset_n", Pins("M5"), IOStandard("SSTL15")),
        Misc("SLEW=FAST"),
    ),
]

_connectors = []

class Platform(XilinxPlatform):
    name = "narvi"
    default_clk_name = "clk100"
    default_clk_period = 10.0

    # From https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf
    # 17,536,096 bits == 2192012 bytes == 0x21728C -- Therefore 0x220000
    gateware_size = 0x220000

    # Numonyx N25Q128A 
    spiflash_read_dummy_bits = 10
    spiflash_clock_div = 4
    spiflash_total_size = int((128/8)*1024*1024) # 128Mbit
    spiflash_page_size = 256
    spiflash_sector_size = 0x10000
    spiflash_model = "n25q128"

    def __init__(self, toolchain="vivado", programmer="openocd"):
        XilinxPlatform.__init__(self, "xc7s50csga324-1", _io, _connectors,
                                toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 34]")


    def create_programmer(self):
        if self.programmer == "openocd":
            proxy="bscan_spi_{}.bit".format(self.device.split('-')[0])
            return OpenOCD(config="board/numato_narvi.cfg", flash_proxy_basename=proxy)
        elif self.programmer == "xc3sprog":
            return XC3SProg("nexys4")
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4") 
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))
        

