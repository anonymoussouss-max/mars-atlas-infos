# Sol 2538 RAD–REMS provisional matches

## Status

The requested header-LMST interval join has been completed. It is provisional, not a validated simultaneous dataset: RAD and REMS clock fields disagree. Do not use these pairings for final scientific inference until that discrepancy is resolved.

RAD observation 00 has UTC 2019-09-26 08:25:42 and START_OBS_MARS 2538 00:15:58. The REMS label starts at UTC 2019-09-26 08:23:55.250, where the table starts at LMST 2538 00:01:07.131. Interpolating the REMS label start/stop UTC anchors against its first/last LMST gives approximately 00:02:51 at the RAD UTC start—about 13 minutes 7 seconds earlier than the RAD Mars header. This is a diagnostic approximation, not a SPICE conversion. No corrective offset was applied. The RAD SIS calls the Mars header LMST, so similarity to REMS LTST is insufficient evidence to relabel it as LTST.

The RAD header wraps from late evening to 00:04:55 while retaining sol 2538. A single sol increment was inferred for that final dose observation using chronological order; the original header is retained. It is outside the supplied REMS range, and was not paired to the beginning of sol 2538.

## Results

- 88 RAD dose observations; 85 with QC 00000000.
- 44 have at least one REMS row under the requested LMST join; 42 of these have RAD QC 00000000.
- 28,364 paired REMS samples out of 31,129 input rows.
- No REMS sample is paired to more than one RAD observation.
- Remaining observations have no samples within the requested windows; no gaps are filled.

## Files

- observations.json: One record per dose observation, both dose rates, original times, QC, match counts, descriptive environmental means, and counts of sensor flag values. Metadata contains units and method.
- paired_rows.jsonl: One JSON object per paired REMS sample, all 40 named REMS fields, source row number, RAD observation ID, dose rates and QC. Original -999 values remain intact.
- match.py: Reproducible Python standard-library script. Run with --input pointing to the original source-file directory and --output pointing to a destination directory. Source filenames must match the uploaded names.

## Matching and quality handling

Windows include the start and exclude the end. OBS_DURATION is converted from SI seconds into LMST clock seconds by multiplying by 86400/88775.244. Mars time is represented as sol*86400 plus clock seconds. Dose units are microGray/hour per the supplied RAD label.

PHA-only observation sections are excluded because they have no dose rate. RAD quality flags are preserved, not automatically discarded. Descriptive means exclude -999 values but do not apply sensor-specific confidence filters; raw flags are preserved so such filters can be applied explicitly. In particular, not every zero in a REMS confidence string denotes invalid data: some encode instrument state. These means are not quality-screened scientific results. Repeated dose values in the paired file represent one RAD measurement, not independent dose measurements.

## Timing references

- RAD RDR SIS, section 4.2.1.2 (Mars header described as LMST): https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/DOCUMENT/RAD_RDR_SIS.HTM
- NASA Mars24 technical notes (mean sol duration): https://www.giss.nasa.gov/tools/mars24/help/notes.html
- The uploaded REMS label and MODRDR6.FMT.txt define the table timestamps and environmental columns.
