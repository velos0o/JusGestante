import streamlit as st
import pandas as pd

class MetricsDisplay:
    """
    Classe para exibir métricas padronizadas em diferentes páginas
    """
    
    @staticmethod
    def show_metrics_grid(metrics_data, num_columns=2):
        """
        Exibe uma grade de métricas
        
        Args:
            metrics_data (list): Lista de tuplas (título, valor, delta)
            num_columns (int): Número de colunas da grade
        """
        # Criar colunas
        cols = st.columns(num_columns)
        
        # Distribuir métricas pelas colunas
        for i, (title, value, delta) in enumerate(metrics_data):
            col_idx = i % num_columns
            with cols[col_idx]:
                st.metric(title, value, delta)
    
    @staticmethod
    def pendencias_metrics(data, pendencias_field, data_field):
        """
        Exibe métricas específicas para pendências
        
        Args:
            data (pd.DataFrame): DataFrame com os dados
            pendencias_field (str): Nome do campo de pendências
            data_field (str): Nome do campo de data
        """
        # Calcular métricas
        total_registros = len(data)
        pendencias_count = data[pendencias_field].notna().sum()
        data_count = data[data_field].notna().sum()
        
        if total_registros > 0:
            pendencias_percent = (pendencias_count / total_registros) * 100
            data_percent = (data_count / total_registros) * 100
        else:
            pendencias_percent = 0
            data_percent = 0
        
        # Preparar dados das métricas
        metrics_data = [
            ("Total de Registros", total_registros, None),
            ("Registros com Pendências", pendencias_count, f"{pendencias_percent:.1f}%"),
            ("Registros com Data Marcada", data_count, f"{data_percent:.1f}%"),
            ("Percentual com Pendências", f"{pendencias_percent:.1f}%", None)
        ]
        
        # Exibir métricas
        MetricsDisplay.show_metrics_grid(metrics_data)
        
    @staticmethod
    def status_distribution(data, field_name, title="Distribuição por Status"):
        """
        Exibe um gráfico de barras com a distribuição de status
        
        Args:
            data (pd.DataFrame): DataFrame com os dados
            field_name (str): Nome do campo para contagem
            title (str): Título do gráfico
        """
        st.subheader(title)
        
        if field_name in data.columns:
            status_counts = data[field_name].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            st.bar_chart(status_counts.set_index('Status')) 