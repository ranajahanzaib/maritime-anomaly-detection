# Scientific Limitations & Ethical Considerations

## 1. Distinction Between Telemetry Anomalies and Illicit Intent

- **Anomalies are not accusations:** An unusual speed, loitering period, or rendezvous observation does not indicate illegal or hostile activity.
- **Normal operational explanations:** Legitimate maritime operations frequently generate statistical deviations:
  - Weather avoidance, heavy sea rerouting, and bunkering.
  - Port congestion, tidal waiting, and mechanical drift.
  - Search and Rescue (SAR) missions or law enforcement patrols.
  - Routine tug escorts, bunkering barges, and pilot transfers.
- **The platform's role:** The system flags statistical and spatial deviations and exposes the evidence to support human investigation, rather than rendering automated verdicts.

---

## 2. AIS Transmission Gaps as Observability Signals

- **VHF line-of-sight & receiver limits:** AIS operates in the VHF maritime band. Land topography, coastal distance, antenna shading, and satellite constellation pass intervals naturally cause message drops.
- **Silent interpolation prohibited:** The platform strictly prohibits interpolating across long gaps (>45 min) to prevent fabricating false tracks across separation zones or geographic hazards.

---

## 3. Ground-Truth Dataset Scope

- Annotated datasets such as HawaiiCoast_GT and Danish AIS provide localized operational contexts and limited sample sizes. Benchmark detection scores on these datasets cannot be extrapolated as universal global detection guarantees.
- Synthetic demonstration data is provided for deterministic testing and reproducible demonstration, clearly tagged as `is_synthetic=True`.
