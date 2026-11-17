# Behavioral Detection Methods & Contextual Reasoning

The platform implements a multi-tier detection architecture combining rule-based heuristics, statistical baseline profiling, unsupervised feature outliers, and deep temporal sequence modeling.

---

## 1. Loitering and Dwell Detector (`LoiteringDetector`)

- **Criteria:** SOG $\le 1.5$ knots within a spatial radius $\le 1.2$ NM for $\ge 2.0$ hours.
- **Contextual Differentiation:**
  - **Inside Designated Anchorage:** Evaluated as `EXPECTED_CONTEXT` (normal waiting, bunkering, or crew transfer).
  - **Inside Port Limits:** Evaluated as `EXPECTED_CONTEXT` (berthing queue or port congestion).
  - **Fishing Vessel in Open Sea:** Identified as legitimate trawling operations.
  - **Open Water Dwell:** Flagged as `POTENTIALLY_RELEVANT` for analyst review.

---

## 2. Rendezvous Detector (`RendezvousDetector`)

- **Criteria:** Synchronous observations between two vessels with inter-vessel distance $\le 600\text{ meters}$, duration $\ge 15\text{ minutes}$, and low relative speed $\le 4.0\text{ knots}$.
- **Contextual Differentiation:**
  - **In Port or Anchorage involving Tug/Pilot:** Tagged as `EXPECTED_CONTEXT` (routine tug assist or pilot boarding).
  - **In Open Sea:** Tagged as `POTENTIALLY_RELEVANT` (unclassified encounter or ship-to-ship transfer).
- **Evidence Payload:** Full pairwise distance timeline, relative velocity, and course difference over time.

---

## 3. Route Corridor Deviation (`RouteDeviationDetector`)

- **Criteria:** Lateral departure $\ge 3.5\text{ NM}$ from established traffic separation schemes (TSS) or learned fairway centerlines.
- **Evidence Payload:** Waypoints of expected shipping corridor alongside actual peak deviation coordinates.

---

## 4. Peer-Group Deviation (`PeerGroupDeviationDetector`)

- **Criteria:** Evaluates kinematic profiles against vessel type baseline distributions:
  $$z = \frac{|\bar{v}_{\text{obs}} - \mu_{\text{peer}}|}{\sigma_{\text{peer}}}$$
  Flagged when $z \ge 2.5$ or when $p_{95}$ speed exceeds the class ceiling.

---

## 5. Historical Inconsistency (`HistoricalInconsistencyDetector`)

- **Criteria:** Requires $\ge 30$ historical observations for a vessel to establish a baseline profile. Flags speed regime shifts ($>8\text{ kts}$ shift) or operations far outside historical operating radii ($>2.5 \times r_{\text{home}}$).

---

## 6. AIS Transmission Gap (`AISTransmissionGapDetector`)

- **Criteria:** Silence interval $\ge 2.0\text{ hours}$.
- **Principle:** Data quality and RF observability signal. Never treated as proof of intent or illegal activity.
