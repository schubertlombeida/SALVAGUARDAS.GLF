"""Crea un ZIP académico acotado desde la entrega ejecutada, sin modificarla."""
import argparse
import csv
import hashlib
import json
import math
import zipfile
from pathlib import Path

REQUIRED=(
    'LEEME.md','overfitting_analysis.ipynb','requirements.txt',
    'data/revision_semana3_IA.json','src/experiment.py','src/build_delivery.py',
    'results/base_history.csv','results/regularizacion_l2_history.csv',
    'results/early_stopping_history.csv','results/comparison.csv',
    'results/cv_results.json','results/metrics.json',
    'results/split_audit.json','results/split_manifest.csv',
    'results/reports/diagnostic_report.pdf',
    'results/figures/01_base.png','results/figures/02_regularizacion_l2.png',
    'results/figures/03_early_stopping.png','results/figures/04_curvas_avanzadas.png',
    'results/figures/05_comparacion.png',
)
PREFIX='ENTREGA_SEMANA_3/'

def sha(data):return hashlib.sha256(data).hexdigest()

def check_source(source):
    source=Path(source)
    data={name:(source/name).read_bytes() for name in REQUIRED}
    notebook=json.loads(data['overfitting_analysis.ipynb'])
    code=[c for c in notebook['cells'] if c['cell_type']=='code']
    if len(code)!=9 or any(c.get('execution_count') is None or any(o.get('output_type')=='error' for o in c.get('outputs',[])) for c in code):
        raise ValueError('Notebook sin las nueve celdas ejecutadas o con errores')
    required_terms=('SGDClassifier','learning_curve','validation_curve','early_stopping')
    code_text=data['src/experiment.py'].decode('utf-8')
    if any(term not in code_text for term in required_terms):
        raise ValueError('Falta implementación del experimento')
    metrics=json.loads(data['results/metrics.json'])
    comparisons=list(csv.DictReader(data['results/comparison.csv'].decode('utf-8-sig').splitlines()))
    if len(comparisons)!=9:
        raise ValueError('Comparación base/L2/early stopping incompleta')
    for row in comparisons:
        actual=metrics['models'][row['model']][row['split']]
        for metric in ('loss','accuracy','balanced_accuracy','macro_f1'):
            if not math.isclose(float(row[metric]),float(actual[metric]),rel_tol=0,abs_tol=1e-10):
                raise ValueError(f'Comparación inconsistente: {row["model"]}/{row["split"]}/{metric}')
    for name in ('base','regularizacion_l2','early_stopping'):
        history=list(csv.DictReader(data[f'results/{name}_history.csv'].decode('utf-8-sig').splitlines()))
        if len(history)!=metrics['models'][name]['parameters']['epochs_run']:
            raise ValueError(f'Historial incompleto: {name}')
    if not data['results/reports/diagnostic_report.pdf'].startswith(b'%PDF-'):
        raise ValueError('Reporte PDF inválido')
    if any(not data[name].startswith(b'\x89PNG\r\n\x1a\n') for name in REQUIRED if name.endswith('.png')):
        raise ValueError('Figura PNG inválida')
    return data

def build(source,output):
    source,output=Path(source),Path(output)
    data=check_source(source)
    before={name:sha(content) for name,content in data.items()}
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name in REQUIRED:
            info=zipfile.ZipInfo(PREFIX+name,date_time=(2026,10,3,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16
            archive.writestr(info,data[name],compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist())!={PREFIX+x for x in REQUIRED}:
            raise ValueError('Contenido ZIP distinto del manifiesto')
        if any(sha(archive.read(PREFIX+name))!=before[name] for name in REQUIRED):
            raise ValueError('Un archivo del ZIP no coincide con el original')
    if any(sha((source/name).read_bytes())!=before[name] for name in REQUIRED):
        raise ValueError('El paquete fuente fue modificado')
    return {'zip':str(output.resolve()),'files':len(REQUIRED),'sha256':sha(output.read_bytes()),
            'source_files_unchanged':True,'notebook_executed_cells':9,
            'included_paths':list(REQUIRED)}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',default='../outputs/semana_3/ENTREGA_SEMANA_3')
    p.add_argument('--output',default='../outputs/semana_3/SEMANA_3_ENTREGA_ACADEMICA.zip')
    a=p.parse_args();print(json.dumps(build(a.source,a.output),ensure_ascii=False,indent=2))
