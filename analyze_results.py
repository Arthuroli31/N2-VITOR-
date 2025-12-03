#!/usr/bin/env python3
"""
Script de Análise e Visualização dos Resultados
Gera gráficos e tabelas comparativas para diferentes configurações
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict
import pandas as pd


class ProductionAnalyzer:
    """Analisador de resultados da linha de produção"""
    
    def __init__(self):
        self.reports = []
    
    def load_report(self, filename: str):
        """Carrega um relatório JSON"""
        with open(filename, 'r', encoding='utf-8') as f:
            report = json.load(f)
            self.reports.append(report)
            return report
    
    def create_comparison_table(self) -> pd.DataFrame:
        """Cria tabela comparativa dos resultados"""
        data = []
        
        for i, report in enumerate(self.reports):
            config = report['configuracao']
            results = report['resultados']
            perf = report['desempenho']
            
            data.append({
                'Configuração': i + 1,
                'Buffer': config['capacidade_buffer'],
                'Produtores': config['num_produtores'],
                'Consumidores': config['num_consumidores'],
                'Timesteps': config['total_timesteps'],
                'Produzido': results['total_produzido'],
                'Consumido': results['total_consumido'],
                'Restante': results['itens_restantes_buffer'],
                'Tempo (s)': perf['tempo_execucao_segundos'],
                'Taxa Prod/s': perf['taxa_producao_por_segundo'],
                'Taxa Cons/s': perf['taxa_consumo_por_segundo']
            })
        
        df = pd.DataFrame(data)
        return df
    
    def plot_buffer_evolution(self, report: dict, title: str = "Evolução do Buffer"):
        """Plota a evolução do tamanho do buffer ao longo do tempo"""
        snapshots = report.get('buffer_snapshots', [])
        
        if not snapshots:
            print("Sem dados de snapshots do buffer")
            return
        
        plt.figure(figsize=(12, 6))
        plt.plot(snapshots, linewidth=2, color='#2E86AB')
        plt.axhline(y=report['configuracao']['capacidade_buffer'], 
                   color='r', linestyle='--', label='Capacidade Máxima')
        plt.xlabel('Snapshot (intervalos de tempo)', fontsize=12)
        plt.ylabel('Itens no Buffer', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        filename = title.lower().replace(' ', '_') + '.png'
        plt.savefig(filename, dpi=300)
        print(f"Gráfico salvo: {filename}")
        plt.close()
    
    def plot_production_vs_consumption(self, report: dict, 
                                      title: str = "Produção vs Consumo"):
        """Plota comparação entre produção e consumo"""
        results = report['resultados']
        
        categories = ['Produzido', 'Consumido', 'Restante no Buffer']
        values = [
            results['total_produzido'],
            results['total_consumido'],
            results['itens_restantes_buffer']
        ]
        colors = ['#06A77D', '#F77F00', '#D62828']
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, values, color=colors, alpha=0.8)
        plt.ylabel('Quantidade de Itens', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, axis='y', alpha=0.3)
        
        # Adiciona valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        filename = title.lower().replace(' ', '_') + '.png'
        plt.savefig(filename, dpi=300)
        print(f"Gráfico salvo: {filename}")
        plt.close()
    
    def plot_wait_times(self, report: dict, 
                       title: str = "Tempos de Espera"):
        """Plota tempos de espera de produtores e consumidores"""
        results = report['resultados']
        
        categories = ['Esperas\nProdutores', 'Esperas\nConsumidores']
        values = [
            results['esperas_produtores'],
            results['esperas_consumidores']
        ]
        colors = ['#457B9D', '#E63946']
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(categories, values, color=colors, alpha=0.8)
        plt.ylabel('Número de Esperas', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, axis='y', alpha=0.3)
        
        # Adiciona valores nas barras
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        filename = title.lower().replace(' ', '_') + '.png'
        plt.savefig(filename, dpi=300)
        print(f"Gráfico salvo: {filename}")
        plt.close()
    
    def plot_performance_comparison(self):
        """Plota comparação de desempenho entre diferentes configurações"""
        if len(self.reports) < 2:
            print("Necessário pelo menos 2 relatórios para comparação")
            return
        
        configs = [f"Config {i+1}" for i in range(len(self.reports))]
        prod_rates = [r['desempenho']['taxa_producao_por_segundo'] for r in self.reports]
        cons_rates = [r['desempenho']['taxa_consumo_por_segundo'] for r in self.reports]
        
        x = np.arange(len(configs))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars1 = ax.bar(x - width/2, prod_rates, width, label='Taxa de Produção', 
                      color='#06A77D', alpha=0.8)
        bars2 = ax.bar(x + width/2, cons_rates, width, label='Taxa de Consumo', 
                      color='#F77F00', alpha=0.8)
        
        ax.set_ylabel('Taxa (itens/segundo)', fontsize=12)
        ax.set_title('Comparação de Desempenho entre Configurações', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(configs)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('comparacao_desempenho.png', dpi=300)
        print(f"Gráfico salvo: comparacao_desempenho.png")
        plt.close()
    
    def plot_buffer_capacity_impact(self):
        """Analisa impacto da capacidade do buffer"""
        if len(self.reports) < 2:
            print("Necessário pelo menos 2 relatórios para análise")
            return
        
        buffer_sizes = [r['configuracao']['capacidade_buffer'] for r in self.reports]
        remaining = [r['resultados']['itens_restantes_buffer'] for r in self.reports]
        prod_waits = [r['resultados']['esperas_produtores'] for r in self.reports]
        cons_waits = [r['resultados']['esperas_consumidores'] for r in self.reports]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Gráfico 1: Itens restantes vs capacidade
        ax1.scatter(buffer_sizes, remaining, s=100, alpha=0.6, color='#2E86AB')
        ax1.set_xlabel('Capacidade do Buffer', fontsize=12)
        ax1.set_ylabel('Itens Restantes', fontsize=12)
        ax1.set_title('Impacto da Capacidade do Buffer', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Esperas vs capacidade
        ax2.scatter(buffer_sizes, prod_waits, s=100, alpha=0.6, 
                   color='#457B9D', label='Produtores')
        ax2.scatter(buffer_sizes, cons_waits, s=100, alpha=0.6, 
                   color='#E63946', label='Consumidores')
        ax2.set_xlabel('Capacidade do Buffer', fontsize=12)
        ax2.set_ylabel('Número de Esperas', fontsize=12)
        ax2.set_title('Esperas vs Capacidade do Buffer', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('impacto_capacidade_buffer.png', dpi=300)
        print(f"Gráfico salvo: impacto_capacidade_buffer.png")
        plt.close()
    
    def generate_full_report(self, output_file: str = "analise_completa.txt"):
        """Gera relatório textual completo"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ANÁLISE COMPLETA - SISTEMA DE CONTROLE DE LINHA DE PRODUÇÃO\n")
            f.write("="*80 + "\n\n")
            
            for i, report in enumerate(self.reports):
                f.write(f"\n{'='*80}\n")
                f.write(f"CONFIGURAÇÃO {i+1}\n")
                f.write(f"{'='*80}\n\n")
                
                config = report['configuracao']
                results = report['resultados']
                perf = report['desempenho']
                
                f.write("[PARÂMETROS]\n")
                f.write(f"  Capacidade do Buffer: {config['capacidade_buffer']:,}\n")
                f.write(f"  Número de Produtores: {config['num_produtores']:,}\n")
                f.write(f"  Número de Consumidores: {config['num_consumidores']:,}\n")
                f.write(f"  Total de Timesteps: {config['total_timesteps']:,}\n\n")
                
                f.write("[RESULTADOS]\n")
                f.write(f"  Total Produzido: {results['total_produzido']:,}\n")
                f.write(f"  Total Consumido: {results['total_consumido']:,}\n")
                f.write(f"  Itens Restantes: {results['itens_restantes_buffer']:,}\n")
                f.write(f"  Esperas de Produtores: {results['esperas_produtores']:,}\n")
                f.write(f"  Esperas de Consumidores: {results['esperas_consumidores']:,}\n\n")
                
                f.write("[DESEMPENHO]\n")
                f.write(f"  Tempo de Execução: {perf['tempo_execucao_segundos']:.2f} segundos\n")
                f.write(f"  Taxa de Produção: {perf['taxa_producao_por_segundo']:.2f} itens/s\n")
                f.write(f"  Taxa de Consumo: {perf['taxa_consumo_por_segundo']:.2f} itens/s\n\n")
                
                # Análise
                f.write("[ANÁLISE]\n")
                eficiencia = (results['total_consumido'] / results['total_produzido'] * 100) if results['total_produzido'] > 0 else 0
                f.write(f"  Eficiência de Consumo: {eficiencia:.2f}%\n")
                
                taxa_ocupacao = (results['itens_restantes_buffer'] / config['capacidade_buffer'] * 100)
                f.write(f"  Taxa de Ocupação Final do Buffer: {taxa_ocupacao:.2f}%\n")
                
                ratio = config['num_consumidores'] / config['num_produtores']
                f.write(f"  Razão Consumidores/Produtores: {ratio:.2f}\n\n")
        
        print(f"Relatório completo salvo: {output_file}")


def main():
    """Exemplo de uso do analisador"""
    analyzer = ProductionAnalyzer()
    
    # Carrega relatório do toy problem
    try:
        report = analyzer.load_report('relatorio_toy_problem.json')
        print("Relatório carregado: relatorio_toy_problem.json")
        
        # Gera visualizações
        print("\nGerando visualizações...")
        analyzer.plot_production_vs_consumption(report, "Produção vs Consumo - Toy Problem")
        analyzer.plot_wait_times(report, "Tempos de Espera - Toy Problem")
        
        if report.get('buffer_snapshots'):
            analyzer.plot_buffer_evolution(report, "Evolução do Buffer - Toy Problem")
        
        # Gera relatório textual
        analyzer.generate_full_report("analise_toy_problem.txt")
        
        print("\nAnálise concluída!")
        
    except FileNotFoundError:
        print("Erro: Execute primeiro o production_line.py para gerar os relatórios")


if __name__ == "__main__":
    main()
