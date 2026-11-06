"""Run with the five original source files in --input; Python standard library only."""
import argparse, bisect, collections, datetime as dt, json, pathlib, re, statistics, zipfile

p = argparse.ArgumentParser()
p.add_argument('--input', type=pathlib.Path, required=True)
p.add_argument('--output', type=pathlib.Path, required=True)
a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
rad_name = 'RAD_RDR_2019_269_08_25_2538_V00.TXT'
rems_name = 'RME_622755917RMD25380000000_______P2.TAB.txt'
fmt = (a.input / 'MODRDR6.FMT.txt').read_text()
columns = []
for block in re.findall(r'OBJECT\s*= COLUMN(.*?)END_OBJECT\s*= COLUMN', fmt, re.S):
    def field(name):
        m = re.search(r'^\s*'+name+r'\s*=\s*("[^"]*"|[^\r\n]+)', block, re.M)
        return m[1].strip().strip('"') if m else None
    columns.append(dict(name=field('NAME'), unit=field('UNIT'), start=int(field('START_BYTE'))-1, width=int(field('BYTES')), type=field('DATA_TYPE')))
assert len(columns) == 40
rems = []
for line in (a.input / rems_name).read_text().splitlines():
    row = {}
    for c in columns:
        v = line[c['start']:c['start']+c['width']].strip()
        row[c['name']] = int(v) if c['type']=='ASCII_INTEGER' else float(v) if c['type']=='ASCII_REAL' else v
    rems.append(row)
assert len(rems) == 31129
def mars_seconds(value):
    sol, h, m, s = re.match(r'(\d+)[ M]+(\d+):(\d+):([\d.]+)', value).groups()
    return int(sol)*86400+int(h)*3600+int(m)*60+float(s)
times = [mars_seconds(r['LMST']) for r in rems]
assert all(x<y for x,y in zip(times,times[1:]))
rad = []
for m in re.finditer(r'\[OBSERVATION: (\d+)\]([\s\S]*?)(?=\[OBSERVATION:|\Z)', (a.input/rad_name).read_text()):
    b=m[2]; r={'OBSERVATION':m[1]}
    for k in ['START_OBS_MARS','START_OBS_UTC','OBS_DURATION','QC']:
        r[k]=re.search(r'^'+k+r'=(.*)$', b, re.M)[1].strip().strip('"')
    r['OBS_DURATION']=int(r['OBS_DURATION'])
    for k in ['DOSIMETRY_TOTAL_DOSE_B','DOSIMETRY_TOTAL_DOSE_E']:
        v=re.search(r'\['+k+r': \d+\]\s*([-+\d.eE]+)',b)
        r[k]=float(v[1]) if v else None
    if r['DOSIMETRY_TOTAL_DOSE_B'] is not None: rad.append(r)
assert len(rad)==88
summaries=[]; pairs=[]; previous=None; rollover=0
numeric=[c['name'] for c in columns if c['type']=='ASCII_REAL']
for r in rad:
    raw=mars_seconds(r['START_OBS_MARS'])
    if previous is not None and raw<previous-43200: rollover+=86400
    previous=raw; start=raw+rollover; end=start+r['OBS_DURATION']*86400/88775.244
    lo=bisect.bisect_left(times,start); hi=bisect.bisect_left(times,end)
    matched=rems[lo:hi]
    summary={**r,'timing_status':'provisional_clock_discrepancy_unresolved','rad_qc_zero':r['QC']=='00000000','inferred_sol_rollover':bool(rollover),'window_start_absolute_lmst_seconds':start,'window_end_absolute_lmst_seconds':end,'rems_row_count':len(matched),'rems_first_row_1based':lo+1 if matched else None,'rems_last_row_1based':hi if matched else None,'means_excluding_minus999_only':{},'confidence_flag_counts':{}}
    for k in numeric:
        vals=[x[k] for x in matched if x[k]!=-999.0]
        summary['means_excluding_minus999_only'][k]={'mean':statistics.mean(vals) if vals else None,'count':len(vals)}
    for c in columns:
        if 'CONFIDENCE' in c['name']:
            summary['confidence_flag_counts'][c['name']]=dict(collections.Counter(x[c['name']] for x in matched))
    summaries.append(summary)
    for idx in range(lo,hi):
        pairs.append({'RAD_OBSERVATION':r['OBSERVATION'],'RAD_QC':r['QC'],'RAD_DOSE_B_uGy_h':r['DOSIMETRY_TOTAL_DOSE_B'],'RAD_DOSE_E_uGy_h':r['DOSIMETRY_TOTAL_DOSE_E'],'REMS_ROW_1BASED':idx+1,'REMS':rems[idx]})
assert len({x['REMS_ROW_1BASED'] for x in pairs})==len(pairs)
counts={'rad_dose_observations':len(rad),'rad_qc_zero':sum(r['QC']=='00000000' for r in rad),'with_rems_rows':sum(bool(x['rems_row_count']) for x in summaries),'qc_zero_with_rems_rows':sum(x['rad_qc_zero'] and bool(x['rems_row_count']) for x in summaries),'paired_rems_rows':len(pairs),'rems_input_rows':len(rems)}
metadata={'status':'PROVISIONAL: clock discrepancy unresolved','counts':counts,'method':'RAD header LMST, start inclusive/end exclusive; duration SI seconds converted by 86400/88775.244. One clock wrap inferred from chronological observations; original header retained. No UTC offset correction applied.','quality':'All RAD QC retained. Raw REMS flags and -999 values retained in pairs. Summary means exclude -999 only, with no sensor-specific quality filtering; these are descriptive, not analysis-ready.','units':{c['name']:c['unit'] for c in columns},'sources':[rad_name,rems_name,'MODRDR6.FMT.txt']}
(a.output/'observations.json').write_text(json.dumps({'metadata':metadata,'observations':summaries},indent=2)+'\n')
with (a.output/'paired_rows.jsonl').open('w') as f:
    for row in pairs:f.write(json.dumps(row)+'\n')
print(json.dumps(counts,indent=2))
print('No REMS rows:', [x['OBSERVATION'] for x in summaries if not x['rems_row_count']])
print('First window sample count:',summaries[0]['rems_row_count'])
