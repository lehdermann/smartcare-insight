#
# SmartCare Insight - main.py
#
# Copyright 2025 SmartCare Insight Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from dotenv import load_dotenv

from models import (
    AnalysisType, AnalysisRequest, ComparativeAnalysisRequest, 
    EventBasedAnalysisRequest, TrendAnalysisRequest, AnalysisResponse, HealthCheckResponse,
    PatientData, VitalSign
)
from providers import get_llm_provider, LLMProvider

# Load environment variables
load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "healthcare-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "healthcare")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "healthcare_monitoring")

# Initialize FastAPI app
app = FastAPI(
    title="SmartCare Insight - LLM Service",
    description="API for LLM-based analysis of health monitoring data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
influx_client = None
query_api = None

def get_influxdb_client() -> QueryApi:
    """Get the InfluxDB query API client."""
    global query_api
    if query_api is None:
        setup_influxdb()
    return query_api

def get_llm_service() -> LLMProvider:
    """Get the LLM provider service."""
    return get_llm_provider()

def setup_influxdb():
    """Set up the InfluxDB client."""
    global influx_client, query_api
    
    try:
        # Create InfluxDB client
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Create query API
        query_api = influx_client.query_api()
        
        print(f"Connected to InfluxDB at {INFLUXDB_URL}")
        return True
        
    except Exception as e:
        print(f"Error setting up InfluxDB: {e}")
        return False

async def fetch_patient_data(
    patient_id: str,
    start_time: datetime,
    end_time: datetime,
    measurement_types: Optional[List[str]] = None
) -> PatientData:
    """
    Fetch patient data from InfluxDB.
    
    Parameters:
    -----------
    patient_id : str
        Patient ID
    start_time : datetime
        Start time for data retrieval
    end_time : datetime
        End time for data retrieval
    measurement_types : Optional[List[str]]
        List of measurement types to retrieve, or None for all
        
    Returns:
    --------
    PatientData
        Patient data object with vital signs
    """
    # Convert datetime to RFC3339 format for InfluxDB
    start_rfc = start_time.isoformat() + 'Z'
    end_rfc = end_time.isoformat() + 'Z'
    
    # Construir filtro de tipos de medição
    measurement_condition = ''
    if measurement_types and len(measurement_types) > 0:
        # Criar condições para cada tipo de medição
        conditions = []
        for mtype in measurement_types:
            if mtype in ['hr', 'oxygen', 'bp_sys', 'bp_dia', 'glucose', 'activity']:
                conditions.append(f'r.measurement_type == "{mtype}"')
        
        if conditions:
            measurement_condition = ' or '.join(conditions)
    
    # Consulta para buscar os dados brutos
    flux_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {start_rfc}, stop: {end_rfc})
        |> filter(fn: (r) => r._measurement == "vital_signs")
        |> filter(fn: (r) => r.patient_id == "{patient_id}")
        {f'|> filter(fn: (r) => {measurement_condition})' if measurement_condition else ''}
    '''

    print(f'Query: {flux_query}')
    
    try:
        # Executar consulta
        result = query_api.query(query=flux_query)
        
        # Processar resultados
        vitals = []
        
        # Contadores para depuração
        total_records = 0
        valid_records = 0
        
        for table in result:
            total_records += len(table.records)
            for record in table.records:
                # Ignorar registros de anomalia
                if record.get_field() == 'is_anomaly':
                    continue
                    
                # Criar um VitalSign para cada medição
                try:
                    vital = VitalSign(
                        timestamp=record.get_time(),
                        value=float(record.get_value()),
                        measurement_type=record.values.get('measurement_type', 'unknown'),
                        is_anomaly=record.values.get('is_anomaly', False)
                    )
                    vitals.append(vital)
                    valid_records += 1
                except Exception as e:
                    print(f"Erro ao processar registro: {e}")
                    continue
        
        print(f'Total de registros brutos: {total_records}')
        print(f'Total de registros válidos: {valid_records}')
        
        print(f'Total de registros processados: {len(vitals)}')
        
        # Create and return patient data
        return PatientData(
            patient_id=patient_id,
            vitals=vitals,
            start_time=start_time,
            end_time=end_time
        )
        
    except Exception as e:
        print(f"Error fetching patient data: {e}")
        # Return empty data on error
        return PatientData(
            patient_id=patient_id,
            vitals=[],
            start_time=start_time,
            end_time=end_time
        )

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SmartCare Insight - LLM Service API"}

@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    llm_service: LLMProvider = Depends(get_llm_service)
):
    """Check the health of the LLM service."""
    health_result = await llm_service.health_check()
    return HealthCheckResponse(**health_result)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_patient_data(
    request: AnalysisRequest,
    query_api: QueryApi = Depends(get_influxdb_client),
    llm_service: LLMProvider = Depends(get_llm_service)
):
    """
    Analyze patient data using the LLM service.
    
    This endpoint supports four types of analysis:
    - time_window: Analyze data over a specific time window
    - event_based: Analyze data around specific events
    - comparative: Compare data between two time periods
    - trend_analysis: Analyze trends across multiple time windows
    """
    # Handle different analysis types
    if request.analysis_type == AnalysisType.TREND_ANALYSIS and isinstance(request, TrendAnalysisRequest):
        print("\n" + "🔍" * 40)
        print("📊 INICIANDO PROCESSAMENTO DA ANÁLISE DE TENDÊNCIAS")
        print("📋 Dados da Requisição:")
        print(f"   • Paciente: {request.patient_id}")
        print(f"   • Data/Hora Final: {request.end_time}")
        print(f"   • Tipos de Medição: {', '.join(request.measurement_types) if request.measurement_types else 'Todos'}")
        
        # For trend analysis, we'll create windows and analyze each one
        window_duration = timedelta(hours=request.window_duration_hours)
        window_interval = timedelta(hours=request.window_interval_hours)
        
        print("\n⚙️  Configuração das Janelas:")
        print(f"   • Quantidade: {request.window_count} janelas")
        print(f"   • Duração: {window_duration} cada")
        print(f"   • Intervalo: {window_interval} entre janelas")
        
        # Calculate the total time span needed
        total_time_span = window_duration * request.window_count + window_interval * (request.window_count - 1)
        
        # Override the start_time based on end_time and total time span
        calculated_start_time = request.end_time - total_time_span
        
        print("\n📅 Período Total de Análise:")
        print(f"   • Início: {calculated_start_time}")
        print(f"   • Término: {request.end_time}")
        print(f"   • Duração Total: {total_time_span}")
        print("🔍" * 40 + "\n")
        
        # Create a list to store data for each window
        windows_data = []
        
        # Generate time windows from oldest to newest
        for i in range(request.window_count):
            # Calculate window start and end times
            window_start = calculated_start_time + (window_duration + window_interval) * i
            window_end = window_start + window_duration
            
            # Ensure we don't go beyond the end time
            if window_end > request.end_time:
                window_end = request.end_time
            
            # Log do processamento da janela
            print("\n" + "📊" * 40)
            print(f"🔄 PROCESSANDO JANELA {i+1}/{request.window_count}")
            print("-" * 60)
            print(f"   • Período: {window_start} até {window_end}")
            print(f"   • Duração: {window_end - window_start}")
            
            # Buscar dados para esta janela
            print(f"\n🔍 Buscando dados do paciente {request.patient_id}...")
            start_fetch = datetime.now()
            
            window_data = await fetch_patient_data(
                patient_id=request.patient_id,
                start_time=window_start,
                end_time=window_end,
                measurement_types=request.measurement_types
            )
            
            fetch_duration = (datetime.now() - start_fetch).total_seconds()
            total_records = len(window_data.vitals)
            
            print(f"✅ Dados recebidos em {fetch_duration:.2f}s")
            print(f"   • Total de registros: {total_records}")
            
            # Contar e exibir estatísticas por tipo de medição
            if total_records > 0:
                count_by_type = {}
                value_ranges = {}
                
                # Contar registros e calcular estatísticas iniciais
                for vital in window_data.vitals:
                    m_type = vital.measurement_type
                    if m_type not in count_by_type:
                        count_by_type[m_type] = 0
                        value_ranges[m_type] = []
                    count_by_type[m_type] += 1
                    if hasattr(vital, 'value') and vital.value is not None:
                        value_ranges[m_type].append(vital.value)
                
                # Exibir resumo
                print("\n📊 Estatísticas por Tipo de Medição:")
                for m_type, count in count_by_type.items():
                    values = value_ranges.get(m_type, [])
                    if values:
                        min_val = min(values)
                        max_val = max(values)
                        avg_val = sum(values) / len(values)
                        print(f"   • {m_type.upper()}: {count} registros | "
                              f"Valores: {min_val:.1f} - {max_val:.1f} | "
                              f"Média: {avg_val:.1f}")
                    else:
                        print(f"   • {m_type.upper()}: {count} registros (sem valores numéricos)")
            else:
                print("⚠️  AVISO: Nenhum dado encontrado para esta janela")
            
            print("📊" * 40 + "\n")
            
            # Process measurements
            measurement_data = {}
            for vital in window_data.vitals:
                if vital.measurement_type not in measurement_data:
                    measurement_data[vital.measurement_type] = []
                measurement_data[vital.measurement_type].append(vital)
            
            # Create window info with basic structure
            window_info = {
                "window_index": i,
                "window_label": f"Window {i+1}",
                "start_time": window_start,
                "end_time": window_end,
                "vitals": []
            }
            
            # Add measurement data and statistics
            for measurement_type, vitals in measurement_data.items():
                # Extract only numeric values
                values = [v.value for v in vitals if isinstance(v.value, (int, float))]
                
                if values:  # Only add if we have values
                    window_info[f"{measurement_type}_values"] = values
                    window_info[f"{measurement_type}_avg"] = sum(values) / len(values)
                    window_info[f"{measurement_type}_min"] = min(values)
                    window_info[f"{measurement_type}_max"] = max(values)
                    
                    # Debug log
                    print(f"Added {len(values)} {measurement_type} values")
                    print(f"  Avg: {window_info[f'{measurement_type}_avg']:.2f}, "
                          f"Min: {window_info[f'{measurement_type}_min']:.2f}, "
                          f"Max: {window_info[f'{measurement_type}_max']:.2f}")
            
            # Add to windows list
            windows_data.append(window_info)
            print(f"=== END WINDOW {i+1} ===\n")
        
        # Check if we have data to analyze
        if not windows_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for patient {request.patient_id} in any of the specified time windows"
            )
        
        # Create the main patient data object with the full time range
        patient_data = await fetch_patient_data(
            patient_id=request.patient_id,
            start_time=calculated_start_time,
            end_time=request.end_time,
            measurement_types=request.measurement_types
        )
        
        # Add the windows data to the patient data
        patient_data.windows = windows_data
        patient_data.window_count = request.window_count
        patient_data.window_duration_hours = request.window_duration_hours
        patient_data.window_interval_hours = request.window_interval_hours
        
        # Log do resumo final
        print("\n" + "✅" * 40)
        print("📊 RESUMO DA ANÁLISE DE TENDÊNCIAS")
        print("-" * 60)
        print(f"   • Total de Janelas Processadas: {len(windows_data)}/{request.window_count}")
        
        # Resumo por tipo de medição
        if windows_data:
            # Coletar todas as métricas disponíveis
            all_metrics = set()
            for window in windows_data:
                all_metrics.update([k for k in window.keys() if k.endswith('_avg')])
            
            if all_metrics:
                print("\n📈 Métricas Calculadas:")
                for metric in sorted(all_metrics):
                    # Encontrar valores mínimos e máximos entre as janelas
                    values = [w[metric] for w in windows_data if metric in w]
                    if values:
                        min_val = min(values)
                        max_val = max(values)
                        print(f"   • {metric.replace('_avg', '').upper()}: "
                              f"{min_val:.1f} a {max_val:.1f} (variação entre janelas)")
        
        print("\n🔄 Processamento concluído com sucesso!")
        print("✅" * 40 + "\n")
        
    else:
        # For other analysis types, fetch data normally
        patient_data = await fetch_patient_data(
            patient_id=request.patient_id,
            start_time=request.start_time,
            end_time=request.end_time,
            measurement_types=request.measurement_types
        )
        
        # Check if we have data to analyze
        if not patient_data.vitals:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for patient {request.patient_id} in the specified time range"
            )
        
        # Handle comparative analysis
        if request.analysis_type == AnalysisType.COMPARATIVE and isinstance(request, ComparativeAnalysisRequest):
            # Fetch comparison data
            comparison_data = await fetch_patient_data(
                patient_id=request.patient_id,
                start_time=request.comparison_start_time,
                end_time=request.comparison_end_time,
                measurement_types=request.measurement_types
            )
            
            # Add comparison data to the patient data
            patient_data.comparison_data = comparison_data.vitals
    
    # Generate analysis
    analysis = await llm_service.generate_analysis(
        analysis_type=request.analysis_type,
        patient_data=patient_data
    )
    
    return analysis

@app.post("/analyze/time-window", response_model=AnalysisResponse)
async def analyze_time_window(
    request: AnalysisRequest,
    query_api: QueryApi = Depends(get_influxdb_client),
    llm_service: LLMProvider = Depends(get_llm_service)
):
    """Analyze patient data over a specific time window."""
    # Force analysis type to time_window
    request.analysis_type = AnalysisType.TIME_WINDOW
    
    # Use the common analyze endpoint
    return await analyze_patient_data(request, query_api, llm_service)

@app.post("/analyze/event-based", response_model=AnalysisResponse)
async def analyze_event_based(
    request: EventBasedAnalysisRequest,
    query_api: QueryApi = Depends(get_influxdb_client),
    llm_service: LLMProvider = Depends(get_llm_service)
):
    """Analyze patient data around specific events."""
    # Force analysis type to event_based
    request.analysis_type = AnalysisType.EVENT_BASED
    
    # Use the common analyze endpoint
    return await analyze_patient_data(request, query_api, llm_service)

@app.post("/analyze/comparative", response_model=AnalysisResponse)
async def analyze_comparative(
    request: ComparativeAnalysisRequest,
    query_api: QueryApi = Depends(get_influxdb_client),
    llm_service: LLMProvider = Depends(get_llm_service)
) -> AnalysisResponse:
    """Compare patient data between two time periods."""
    # Force analysis type to comparative
    request.analysis_type = AnalysisType.COMPARATIVE
    
    # Redirect to the main analyze endpoint
    return await analyze_patient_data(request, query_api, llm_service)

@app.post("/analyze/trend-analysis", response_model=AnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    query_api: QueryApi = Depends(get_influxdb_client),
    llm_service: LLMProvider = Depends(get_llm_service)
) -> AnalysisResponse:
    """
    Endpoint para análise de tendências em múltiplas janelas de tempo.
    
    Este endpoint recebe os parâmetros de configuração para a análise de tendências,
    incluindo o número de janelas, duração de cada janela e intervalo entre elas.
    """
    import time
    
    # Registrar o tempo de início
    start_time = time.time()
    
    # Log dos parâmetros recebidos
    print("\n" + "="*80)
    print("=== SOLICITAÇÃO DE ANÁLISE DE TENDÊNCIAS RECEBIDA ===")
    print("-"*80)
    print(f"📋 ID do Paciente: {request.patient_id}")
    print(f"📅 Período de Análise: {request.start_time} até {request.end_time}")
    print(f"🔍 Tipo de Análise: {request.analysis_type}")
    print(f"📊 Tipos de Medição: {', '.join(request.measurement_types) if request.measurement_types else 'Todos'}")
    print("\n⚙️  Configuração das Janelas:")
    print(f"   • Número de Janelas: {request.window_count}")
    print(f"   • Duração de cada Janela: {request.window_duration_hours} horas")
    print(f"   • Intervalo entre Janelas: {request.window_interval_hours} horas")
    print("="*80 + "\n")
    
    # Forçar o tipo de análise para tendência
    request.analysis_type = AnalysisType.TREND_ANALYSIS
    
    try:
        # Processar a análise
        resultado = await analyze_patient_data(request, query_api, llm_service)
        
        # Calcular tempo decorrido
        elapsed_time = time.time() - start_time
        
        # Atualizar o resultado com o tempo decorrido e metadados
        resultado.time_elapsed = round(elapsed_time, 2)
        resultado.metadata.update({
            'processing_timestamp': datetime.utcnow().isoformat(),
            'window_count': len(getattr(resultado, 'windows', [])),
            'window_duration_hours': request.window_duration_hours,
            'window_interval_hours': request.window_interval_hours,
            'measurement_types': request.measurement_types
        })
        
        # Log do resultado
        print("\n" + "="*80)
        print("✅ ANÁLISE DE TENDÊNCIAS CONCLUÍDA COM SUCESSO")
        print("-"*80)
        print(f"⏱️  Tempo total de processamento: {resultado.time_elapsed:.2f} segundos")
        print(f"📊 Total de janelas processadas: {len(getattr(resultado, 'windows', []))}")
        
        # Resumo das janelas processadas
        if hasattr(resultado, 'windows') and resultado.windows:
            print("\n📋 Resumo das Janelas:")
            for i, window in enumerate(resultado.windows, 1):
                start = window.get('start_time', 'N/A')
                end = window.get('end_time', 'N/A')
                metrics = [k for k in window.keys() if k.endswith('_avg')]
                print(f"   • Janela {i}: {start} - {end} | Métricas: {', '.join(metrics)}")
        
        print("="*80 + "\n")
        return resultado
        
    except Exception as e:
        print("\n" + "!"*80)
        print(f"❌ ERRO AO PROCESSAR ANÁLISE DE TENDÊNCIAS: {str(e)}")
        print("!"*80 + "\n")
        raise

@app.on_event("startup")
async def startup_event():
    """Run when the application starts."""
    # Set up InfluxDB
    setup_influxdb()

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    global influx_client
    
    # Close InfluxDB client
    if influx_client:
        influx_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
