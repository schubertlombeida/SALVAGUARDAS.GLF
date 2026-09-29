"""EDA de agregados sin exportar texto ni identificadores personales."""
import argparse
import collections
import json
from pathlib import Path
import zipfile


def load_records(archive, member):
    """Leer JSONL UTF-8 sin separar los caracteres Unicode internos del texto."""
    with zipfile.ZipFile(archive) as source:
        return [json.loads(line) for line in source.read(member).decode('utf-8-sig').split('\n') if line.strip()]


def summarize(archive):
    """Calcular estadísticas agregadas de documentos, pares y fragmentos."""
    docs = load_records(archive, 'corpus_documentos.jsonl')
    chunks = load_records(archive, 'corpus_chunks_rag.jsonl')
    pairs = load_records(archive, 'expedientes_pareados.jsonl')
    if not docs or not chunks or not pairs:
        raise ValueError('El corpus requiere documentos, fragmentos y expedientes.')
    ids = {d['document_id'] for d in docs}
    if len(ids) != len(docs) or any(c['document_id'] not in ids for c in chunks):
        raise ValueError('Identificadores documentales duplicados o referencias rotas.')
    splits = collections.defaultdict(set)
    for row in docs + chunks:
        splits[row['project_code']].add(row['split'])
    if any(len(values) != 1 for values in splits.values()):
        raise ValueError('Un expediente aparece en particiones diferentes.')
    count = lambda rows, key: dict(sorted(collections.Counter(r[key] for r in rows).items()))
    lengths = [len(c['text'].split()) for c in chunks]
    bins = {'1-249': 0, '250-499': 0, '500-749': 0, '750 o más': 0}
    for n in lengths:
        if n <= 0:
            raise ValueError('Existe un fragmento vacío.')
        bins['1-249' if n < 250 else '250-499' if n < 500 else '500-749' if n < 750 else '750 o más'] += 1
    return {'documents': len(docs), 'projects': len(pairs), 'chunks': len(chunks),
            'document_words': sum(len(d['text'].split()) for d in docs),
            'roles': count(docs, 'document_role'), 'languages': count(docs, 'language'),
            'groups': count(docs, 'source_group'), 'project_splits': count(pairs, 'split'),
            'chunk_splits': count(chunks, 'split'), 'chunk_lengths': bins}


def figures(metrics, output):
    """Crear seis figuras vectoriales con ReportLab, usando solo agregados."""
    from reportlab.graphics import renderSVG
    from reportlab.graphics.charts.barcharts import HorizontalBarChart
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.lib import colors
    specs = [('roles', 'Documentos por función'), ('languages', 'Documentos por idioma declarado'),
             ('groups', 'Documentos por grupo'), ('project_splits', 'Expedientes por partición'),
             ('chunk_splits', 'Fragmentos por partición'), ('chunk_lengths', 'Longitud de fragmentos en palabras')]
    output.mkdir(parents=True, exist_ok=True)
    for i, (key, title) in enumerate(specs, 1):
        values = metrics[key]
        d = Drawing(640, 260)
        d.add(String(20, 237, title, fontName='Helvetica-Bold', fontSize=14))
        chart = HorizontalBarChart()
        chart.x, chart.y, chart.width, chart.height = 200, 40, 370, 170
        chart.data = [list(values.values())]
        chart.categoryAxis.categoryNames = list(values)
        chart.categoryAxis.labels.fontSize = 10
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(values.values()) * 1.2
        chart.bars[0].fillColor = colors.HexColor('#255f70')
        chart.barLabelFormat = '%d'
        chart.barLabels.boxAnchor = 'w'
        chart.barLabels.dx = 4
        d.add(chart)
        d.add(String(200, 13, 'Fuente: dataset GLF. Recuentos calculados; no son resultados del RAG.', fontSize=8))
        renderSVG.drawToFile(d, str(output / f'{i:02d}_{key}.svg'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--output', default=Path('results'), type=Path)
    args = parser.parse_args()
    metrics = summarize(args.archive)
    (args.output / 'metrics').mkdir(parents=True, exist_ok=True)
    (args.output / 'metrics' / 'eda.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    figures(metrics, args.output / 'figures')
    print(f"EDA completado: {metrics['documents']} documentos, {metrics['projects']} expedientes.")


if __name__ == '__main__':
    main()
