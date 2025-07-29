from gnuradio import gr, blocks, analog
from gnuradio.fft import window, logpwrfft
from gnuradio.filter import firdes
import configparser
import threading
import time
import osmosdr
import signal
import sys
import numpy as np
from gnuradio import zeromq
import logging

CONFIG_PATH = r"D:\django_project\paginajammer\paginajammer\CONFIG.INI"

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler = logging.FileHandler("jammer_debug.log")
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(console_handler)
log = logging.info

log(" Logging iniciado correctamente")
log(" Script JammerP2_NoGui iniciado correctamente")

class JammerNoGUI(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Jammer sin GUI")

        # Leer INI al inicio
        self.config = configparser.ConfigParser()
        self.read_config()

        # Variables
        self.vector_size = 8192
        self.sample_rate_rx = 2e6  # Mejor resolución espectral
        self.sample_rate_tx = self.Samp_Rate_TX
        self.freq = self.frec
        self.bandwidth = self.bandwidth
        self.selector = self.selector_ini
        self.cosine_freq = 20e6

        # SDR Fuente (recepción)
        try:
            self.src = osmosdr.source(args="numchan=1")
        except RuntimeError as e:
            log(f" Error inicializando BladeRF: {e}")
            self.src = None

        self.src.set_sample_rate(self.sample_rate_rx)
        self.src.set_center_freq(self.freq)
        self.src.set_gain(self.rf_gain, 0)
        self.src.set_if_gain(self.if_gain, 0)
        self.src.set_bb_gain(self.bb_gain, 0)
        self.src.set_bandwidth(self.bandwidth, 0)

        # SDR Sumidero (transmisión)
        self.sink = osmosdr.sink(args="numchan=1")
        self.sink.set_sample_rate(self.sample_rate_tx)
        self.sink.set_center_freq(self.freq)
        self.sink.set_gain(self.rf_gain, 0)
        self.sink.set_if_gain(self.if_gain, 0)
        self.sink.set_bb_gain(self.bb_gain, 0)
        self.sink.set_bandwidth(2e6, 0)

        # Generadores de ruido + tonos
        self.tone1 = analog.sig_source_c(20e6, analog.GR_COS_WAVE, self.cosine_freq, 1, 0)
        self.tone2 = analog.sig_source_c(20e6, analog.GR_COS_WAVE, self.cosine_freq, 1, 0.5)
        self.noise1 = analog.fastnoise_source_c(analog.GR_GAUSSIAN, 1, 0, self.vector_size)
        self.noise2 = analog.fastnoise_source_c(analog.GR_GAUSSIAN, 1, 165, self.vector_size)

        self.mult1 = blocks.multiply_vcc(1)
        self.mult2 = blocks.multiply_vcc(1)
        self.add = blocks.add_vcc(1)

        self.selector_block = blocks.selector(gr.sizeof_gr_complex, self.selector, 0)
        self.selector_block.set_enabled(True)

        self.null = blocks.null_source(gr.sizeof_gr_complex)

        # logpwrfft para análisis
        self.logpwrfft = logpwrfft.logpwrfft_c(
            sample_rate=self.sample_rate_rx,  
            fft_size=8192,
            ref_scale=2,
            frame_rate=30,
            avg_alpha=0.5,  # ← prueba este
            average=True,
            shift=False
        )


        # ZMQ para graficar en web
        self.zeromq_pub = zeromq.pub_sink(gr.sizeof_float, self.vector_size, "tcp://*:5678", 100, False, -1, '', True, True)

        # Conexiones
        self.connect(self.noise1, (self.mult1, 0))
        self.connect(self.tone1, (self.mult1, 1))
        self.connect(self.noise2, (self.mult2, 0))
        self.connect(self.tone2, (self.mult2, 1))
        self.connect(self.mult1, (self.add, 0))
        self.connect(self.mult2, (self.add, 1))
        self.connect(self.add, (self.selector_block, 0))
        self.connect(self.null, (self.selector_block, 1))
        self.connect(self.selector_block, self.sink)

        self.connect(self.src, self.logpwrfft)
        self.connect(self.logpwrfft, self.zeromq_pub)

        # Lanzar hilo para leer el .ini periódicamente
        self.monitor_thread = threading.Thread(target=self.config_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def read_config(self):
        self.config.read(CONFIG_PATH)
        get = lambda k, d=0: self.config.getfloat("PARAMETROS", k, fallback=d)
        get_bool = lambda k, d=False: self.config.getboolean("PARAMETROS", k, fallback=d)

        self.frec = get("frecuencia", 1e9)
        self.rf_gain = get("RF_Gain", 73)
        self.if_gain = get("IF_Gain", 73)
        self.bb_gain = get("BB_Gain", 0)
        self.bandwidth = get("bandwidth", 28e6)
        self.Samp_Rate_TX = get("Samp_Rate", 20e6)
        self.selector_ini = 1 if get_bool("selector", False) else 0

    def config_monitor_loop(self):
        last_config = {}
        while True:
            try:
                self.read_config()
                new_config = {
                    "frec": self.frec,
                    "rf_gain": self.rf_gain,
                    "selector": self.selector_ini
                }
                if new_config != last_config:
                    log(f" Cambios detectados en CONFIG.INI -> Aplicando: {new_config}")
                    self.apply_config()
                    last_config = new_config
            except Exception as e:
                log(f"[!] Error leyendo CONFIG.INI: {e}")
            time.sleep(2)

    def apply_config(self):
        self.src.set_center_freq(self.frec)
        self.sink.set_center_freq(self.frec)
        self.sink.set_gain(self.rf_gain, 0)
        self.selector_block.set_input_index(self.selector_ini)

def main():
    tb = JammerNoGUI()
    tb.start()

    def stop_handler(sig, frame):
        log(" Detenido")
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    log(" Jammer activo sin GUI... (Ctrl+C para detener)")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()