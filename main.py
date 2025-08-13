# -*- coding: utf-8 -*-
from sa_api import *
import numpy as np
import time
import threading
from datetime import datetime
import os
import sys

def set_high_priority():
    """Configura alta prioridad del proceso para mejor timing"""
    try:
        import psutil
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
    except:
        pass

def set_timer_resolution():
    """Mejora la resolución del timer en Windows"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # Configurar resolución de timer a 1ms
        winmm = ctypes.windll.winmm
        winmm.timeBeginPeriod.argtypes = [wintypes.UINT]
        winmm.timeBeginPeriod.restype = wintypes.UINT
        winmm.timeEndPeriod.argtypes = [wintypes.UINT]
        winmm.timeEndPeriod.restype = wintypes.UINT
        
        return result == 0
    except:
        return False

class PrecisionTimer:
    """Timer de alta precisión para muestreo constante"""
    
    def __init__(self, target_frequency=50.0):
        self.target_frequency = target_frequency
        self.target_interval = 1.0 / target_frequency
        self.start_time = None
        self.sample_count = 0
        self.timing_errors = []
        
    def start(self):
        """Inicia el timer"""
        self.start_time = time.perf_counter()
        self.sample_count = 0
        self.timing_errors = []
        
    def wait_for_next_sample(self):
        """Espera hasta el siguiente momento de muestreo"""
        if self.start_time is None:
            self.start()
            
        # Tiempo teórico del siguiente sample
        target_time = self.start_time + (self.sample_count + 1) * self.target_interval
        current_time = time.perf_counter()
        
        wait_time = target_time - current_time
        
        # Si estamos retrasados, continuar sin registrar
        if wait_time < 0:
            pass
        else:
            # Espera activa para los últimos microsegundos
            if wait_time > 0.001:  # Si hay más de 1ms, usar sleep
                time.sleep(wait_time - 0.0005)  # Despertar 0.5ms antes
            
            # Espera activa para máxima precisión
            while time.perf_counter() < target_time:
                pass
                
        self.sample_count += 1
        return time.perf_counter()

def power_vs_time_50hz_optimized():
    """Adquisición de potencia optimizada a exactamente 50 Hz"""
    
    # Configuraciones de optimización
    set_high_priority()
    set_timer_resolution()
    
    # Configuración del analizador
    center_freq = 3.4e9
    span = 100e3
    rbw = 30e3
    measurement_time = 6000  # segundos
    calibration_offset_db = 14.6
    target_frequency = 50.0  # Hz exactos
    
    # Crear timer de precisión
    precision_timer = PrecisionTimer(target_frequency)
    
    # Archivo de salida
    now = datetime.now()
    output_file = "{:02d}{:02d}{:02d}.txt".format(now.hour, now.minute, now.second)
    
    handle = sa_open_device()["handle"]
    
    try:
        # Configuración del analizador
        sa_config_center_span(handle, center_freq, span)
        sa_config_level(handle, 0.0)
        sa_config_sweep_coupling(handle, rbw, rbw, 0)
        sa_config_acquisition(handle, SA_AVERAGE, SA_LOG_SCALE)
        sa_initiate(handle, SA_SWEEPING, 0)
        
        sweep_info = sa_query_sweep_info(handle)
        bin_size = sweep_info["bin_size"]
        bin_size_mw = bin_size / 1e6
        log10_conversion = 10.0
        
        # Pre-calentamiento del sistema
        for _ in range(10):
            sa_get_sweep_32f(handle)
        
        with open(output_file, "w") as f_out:
            
            # Iniciar timer de precisión
            start_time = time.perf_counter()
            unix_start = time.time()
            precision_timer.start()
            
            sample_count = 0
            
            while (time.perf_counter() - start_time) < measurement_time:
                # Esperar al siguiente momento de muestreo
                measurement_time_point = precision_timer.wait_for_next_sample()
                
                # Realizar la medición
                sweep_data = sa_get_sweep_32f(handle)["max"]
                
                # Calcular potencia total
                power_linear = np.power(10.0, np.array(sweep_data) / log10_conversion)
                total_power_mw = np.sum(power_linear) * bin_size_mw
                total_power_dbm = (log10_conversion * np.log10(total_power_mw) + calibration_offset_db
                                   if total_power_mw > 0 else -120 + calibration_offset_db)
                
                # Timestamp Unix
                unix_timestamp = unix_start + (measurement_time_point - start_time)
                
                # Escribir solo timestamp Unix y potencia
                f_out.write(f"{unix_timestamp:.6f}\t{total_power_dbm:.2f}\n")
                
                sample_count += 1
            
            # Estadísticas finales
            elapsed = time.perf_counter() - start_time
            actual_frequency = sample_count / elapsed
    
    finally:
        sa_close_device(handle)

def analyze_timing_file(filename):
    """Analiza un archivo de timing para verificar la estabilidad"""
    try:
        data = np.loadtxt(filename, delimiter='\t', skiprows=1)
        timestamps = data[:, 0]
        
        # Calcular intervalos
        intervals = np.diff(timestamps) * 1000  # en ms
        target_interval = 20.0  # ms para 50 Hz
        
        print(f"\n=== ANÁLISIS DE ARCHIVO: {filename} ===")
        print(f"Muestras: {len(timestamps)}")
        print(f"Duración: {timestamps[-1] - timestamps[0]:.2f} s")
        print(f"Intervalo objetivo: {target_interval:.1f} ms")
        print(f"Intervalo promedio: {np.mean(intervals):.3f} ms")
        print(f"Desviación estándar: {np.std(intervals):.3f} ms")
        print(f"Intervalo mínimo: {np.min(intervals):.3f} ms")
        print(f"Intervalo máximo: {np.max(intervals):.3f} ms")
        print(f"Jitter máximo: {np.max(np.abs(intervals - target_interval)):.3f} ms")
        
        # Histograma de intervalos
        within_1ms = np.sum(np.abs(intervals - target_interval) < 1.0)
        within_100us = np.sum(np.abs(intervals - target_interval) < 0.1)
        
        print(f"Muestras dentro de ±1ms: {within_1ms}/{len(intervals)} ({within_1ms/len(intervals)*100:.1f}%)")
        print(f"Muestras dentro de ±100μs: {within_100us}/{len(intervals)} ({within_100us/len(intervals)*100:.1f}%)")
        
    except Exception as e:
        print(f"Error analizando archivo: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        if len(sys.argv) > 2:
            analyze_timing_file(sys.argv[2])
        else:
            print("Uso: python script.py analyze archivo.txt")
    else:
        power_vs_time_50hz_optimized()