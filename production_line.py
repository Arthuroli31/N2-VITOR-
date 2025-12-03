#!/usr/bin/env python3
"""
Sistema de Controle para Linha de Produção Industrial
Miniprojeto Distribuído N2

Implementa o padrão Produtor-Consumidor com threads, semáforos e mutex
para simular uma linha de produção industrial automatizada.
"""

import threading
import time
import queue
import random
from dataclasses import dataclass
from typing import List
import json


@dataclass
class ProductionStats:
    """Estatísticas da produção"""
    total_produced: int = 0
    total_consumed: int = 0
    producer_waits: int = 0
    consumer_waits: int = 0
    buffer_snapshots: List[int] = None
    
    def __post_init__(self):
        if self.buffer_snapshots is None:
            self.buffer_snapshots = []


class ProductionLine:
    """
    Linha de produção industrial com buffer limitado.
    Implementa sincronização usando semáforos e mutex.
    """
    
    def __init__(self, buffer_capacity: int, num_producers: int, 
                 num_consumers: int, total_timesteps: int, validate: bool = True):
        """
        Inicializa a linha de produção.
        
        Args:
            buffer_capacity: Capacidade máxima do buffer
            num_producers: Número de threads produtoras
            num_consumers: Número de threads consumidoras
            total_timesteps: Número total de ciclos de simulação
            validate: Se True, valida os parâmetros mínimos (padrão: True)
        """
        # Validação dos parâmetros (apenas se validate=True)
        if validate:
            if buffer_capacity < 1000:
                raise ValueError("Capacidade do buffer deve ser no mínimo 1000")
            if num_producers < 200:
                raise ValueError("Número de produtores deve ser no mínimo 200")
            min_consumers = int(num_producers * 1.1)
            if num_consumers < min_consumers:
                raise ValueError(f"Número de consumidores deve ser no mínimo {min_consumers}")
            if total_timesteps < 1000000:
                raise ValueError("Número de timesteps deve ser no mínimo 1.000.000")
        
        # Parâmetros da simulação
        self.buffer_capacity = buffer_capacity
        self.num_producers = num_producers
        self.num_consumers = num_consumers
        self.total_timesteps = total_timesteps
        
        # Buffer (fila de processamento)
        self.buffer = []
        
        # Mutex para acesso exclusivo ao buffer
        self.mutex = threading.Lock()
        
        # Semáforo de espaço disponível (inicialmente = capacidade do buffer)
        self.empty_slots = threading.Semaphore(buffer_capacity)
        
        # Semáforo de itens disponíveis (inicialmente = 0)
        self.filled_slots = threading.Semaphore(0)
        
        # Controle de execução
        self.current_timestep = 0
        self.running = True
        self.timestep_lock = threading.Lock()
        
        # Estatísticas
        self.stats = ProductionStats()
        self.stats_lock = threading.Lock()
        
        # Threads
        self.producer_threads = []
        self.consumer_threads = []
        
        # Tempo de início
        self.start_time = None
        self.end_time = None
        
        # Snapshot do buffer a cada N timesteps
        self.snapshot_interval = max(1, total_timesteps // 100)
    
    def get_current_timestep(self) -> int:
        """Retorna o timestep atual de forma thread-safe"""
        with self.timestep_lock:
            return self.current_timestep
    
    def increment_timestep(self) -> int:
        """Incrementa e retorna o timestep atual"""
        with self.timestep_lock:
            self.current_timestep += 1
            return self.current_timestep
    
    def should_continue(self) -> bool:
        """Verifica se a simulação deve continuar"""
        return self.running and self.get_current_timestep() < self.total_timesteps
    
    def producer_task(self, producer_id: int):
        """
        Tarefa executada por cada thread produtora.
        
        Args:
            producer_id: Identificador único do produtor
        """
        while self.should_continue():
            # Aguarda espaço disponível no buffer
            self.empty_slots.acquire()
            
            if not self.should_continue():
                self.empty_slots.release()
                break
            
            # Acesso exclusivo ao buffer
            with self.mutex:
                if len(self.buffer) < self.buffer_capacity:
                    # Produz uma peça (representada por um número único)
                    timestep = self.increment_timestep()
                    piece_id = f"P{producer_id}-T{timestep}"
                    self.buffer.append(piece_id)
                    
                    # Atualiza estatísticas
                    with self.stats_lock:
                        self.stats.total_produced += 1
                        
                        # Snapshot do buffer
                        if timestep % self.snapshot_interval == 0:
                            self.stats.buffer_snapshots.append(len(self.buffer))
                else:
                    # Buffer cheio, registra espera
                    with self.stats_lock:
                        self.stats.producer_waits += 1
            
            # Sinaliza que há um item disponível
            self.filled_slots.release()
            
            # Simula tempo de processamento
            time.sleep(random.uniform(0.0001, 0.0005))
    
    def consumer_task(self, consumer_id: int):
        """
        Tarefa executada por cada thread consumidora.
        
        Args:
            consumer_id: Identificador único do consumidor
        """
        while self.should_continue():
            # Aguarda item disponível no buffer
            self.filled_slots.acquire()
            
            if not self.should_continue():
                self.filled_slots.release()
                break
            
            # Acesso exclusivo ao buffer
            with self.mutex:
                if len(self.buffer) > 0:
                    # Consome uma peça
                    piece_id = self.buffer.pop(0)
                    
                    # Atualiza estatísticas
                    with self.stats_lock:
                        self.stats.total_consumed += 1
                else:
                    # Buffer vazio, registra espera
                    with self.stats_lock:
                        self.stats.consumer_waits += 1
            
            # Sinaliza que há um espaço disponível
            self.empty_slots.release()
            
            # Simula tempo de processamento
            time.sleep(random.uniform(0.0001, 0.0005))
    
    def start(self):
        """Inicia a simulação da linha de produção"""
        print(f"Iniciando simulação da linha de produção...")
        print(f"  Buffer: {self.buffer_capacity} itens")
        print(f"  Produtores: {self.num_producers}")
        print(f"  Consumidores: {self.num_consumers}")
        print(f"  Timesteps: {self.total_timesteps:,}")
        print()
        
        self.start_time = time.time()
        
        # Cria e inicia threads produtoras
        for i in range(self.num_producers):
            thread = threading.Thread(target=self.producer_task, args=(i,), 
                                     name=f"Producer-{i}")
            thread.daemon = True
            self.producer_threads.append(thread)
            thread.start()
        
        # Cria e inicia threads consumidoras
        for i in range(self.num_consumers):
            thread = threading.Thread(target=self.consumer_task, args=(i,), 
                                     name=f"Consumer-{i}")
            thread.daemon = True
            self.consumer_threads.append(thread)
            thread.start()
        
        print("Threads iniciadas. Aguardando conclusão...")
    
    def wait_completion(self):
        """Aguarda a conclusão de todas as threads"""
        # Aguarda até atingir o número de timesteps
        while self.get_current_timestep() < self.total_timesteps:
            time.sleep(0.1)
        
        # Sinaliza para parar
        self.running = False
        
        # Libera semáforos para desbloquear threads em espera
        for _ in range(self.num_producers):
            self.empty_slots.release()
        for _ in range(self.num_consumers):
            self.filled_slots.release()
        
        # Aguarda todas as threads
        for thread in self.producer_threads:
            thread.join(timeout=1.0)
        for thread in self.consumer_threads:
            thread.join(timeout=1.0)
        
        self.end_time = time.time()
        
        print("Simulação concluída!")
    
    def get_report(self) -> dict:
        """
        Gera relatório completo da simulação.
        
        Returns:
            Dicionário com todas as estatísticas
        """
        execution_time = self.end_time - self.start_time if self.end_time else 0
        
        report = {
            "configuracao": {
                "capacidade_buffer": self.buffer_capacity,
                "num_produtores": self.num_producers,
                "num_consumidores": self.num_consumers,
                "total_timesteps": self.total_timesteps
            },
            "resultados": {
                "total_produzido": self.stats.total_produced,
                "total_consumido": self.stats.total_consumed,
                "itens_restantes_buffer": len(self.buffer),
                "esperas_produtores": self.stats.producer_waits,
                "esperas_consumidores": self.stats.consumer_waits
            },
            "desempenho": {
                "tempo_execucao_segundos": round(execution_time, 2),
                "taxa_producao_por_segundo": round(self.stats.total_produced / execution_time, 2) if execution_time > 0 else 0,
                "taxa_consumo_por_segundo": round(self.stats.total_consumed / execution_time, 2) if execution_time > 0 else 0
            },
            "buffer_snapshots": self.stats.buffer_snapshots
        }
        
        return report
    
    def print_report(self):
        """Imprime relatório formatado"""
        report = self.get_report()
        
        print("\n" + "="*70)
        print("RELATÓRIO DA SIMULAÇÃO - LINHA DE PRODUÇÃO INDUSTRIAL")
        print("="*70)
        
        print("\n[CONFIGURAÇÃO]")
        print(f"  Capacidade do Buffer: {report['configuracao']['capacidade_buffer']:,}")
        print(f"  Número de Produtores: {report['configuracao']['num_produtores']:,}")
        print(f"  Número de Consumidores: {report['configuracao']['num_consumidores']:,}")
        print(f"  Total de Timesteps: {report['configuracao']['total_timesteps']:,}")
        
        print("\n[RESULTADOS]")
        print(f"  Total Produzido: {report['resultados']['total_produzido']:,}")
        print(f"  Total Consumido: {report['resultados']['total_consumido']:,}")
        print(f"  Itens Restantes no Buffer: {report['resultados']['itens_restantes_buffer']:,}")
        print(f"  Esperas de Produtores: {report['resultados']['esperas_produtores']:,}")
        print(f"  Esperas de Consumidores: {report['resultados']['esperas_consumidores']:,}")
        
        print("\n[DESEMPENHO]")
        print(f"  Tempo de Execução: {report['desempenho']['tempo_execucao_segundos']:.2f} segundos")
        print(f"  Taxa de Produção: {report['desempenho']['taxa_producao_por_segundo']:.2f} itens/segundo")
        print(f"  Taxa de Consumo: {report['desempenho']['taxa_consumo_por_segundo']:.2f} itens/segundo")
        
        print("\n" + "="*70)
    
    def save_report(self, filename: str = "relatorio_producao.json"):
        """Salva relatório em arquivo JSON"""
        report = self.get_report()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nRelatório salvo em: {filename}")


def main():
    """Função principal - exemplo de uso"""
    
    # Exemplo 1: Toy Problem (para testes rápidos)
    print("="*70)
    print("EXEMPLO 1: TOY PROBLEM (configuração reduzida para teste)")
    print("="*70)
    
    line1 = ProductionLine(
        buffer_capacity=10,
        num_producers=2,
        num_consumers=3,
        total_timesteps=100,
        validate=False  # Desabilita validação para toy problem
    )
    
    line1.start()
    line1.wait_completion()
    line1.print_report()
    line1.save_report("relatorio_toy_problem.json")
    
    print("\n\n")
    
    # Exemplo 2: Configuração Completa (comentado para não executar automaticamente)
    """
    print("="*70)
    print("EXEMPLO 2: CONFIGURAÇÃO COMPLETA")
    print("="*70)
    
    line2 = ProductionLine(
        buffer_capacity=1000,
        num_producers=200,
        num_consumers=220,
        total_timesteps=1000000
    )
    
    line2.start()
    line2.wait_completion()
    line2.print_report()
    line2.save_report("relatorio_completo.json")
    """


if __name__ == "__main__":
    main()
