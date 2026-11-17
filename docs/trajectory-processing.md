# Trajectory Construction & Kinematics Processing

Raw AIS messages are asynchronous, noisy, and prone to signal interruptions. The platform implements rigorous spatial-temporal trajectory processing.

---

## 1. Track Segmentation

- **Time-gap thresholding:** Gaps exceeding `MAX_TIME_GAP_MINUTES` (default 45 minutes) break the trajectory into distinct segments.
- **Why?** Silently interpolating across multi-hour silence fabricates continuous lines across landmasses, separation schemes, or unobserved routes.
- **Handling gaps:** Transmission gaps are isolated as explicit `AIS_TRANSMISSION_GAP` observability records, preserving the last known coordinates, the reappearance coordinates, and the implied displacement velocity.

---

## 2. Geodesic & Kinematic Math

- **Geodesic Distance:** Uses the Haversine great-circle formula:
  $$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
  where $R = 3440.065 \text{ NM}$.

- **Initial Bearing:**
  $$\theta = \text{atan2}\left(\sin \Delta \lambda \cos \phi_2, \; \cos \phi_1 \sin \phi_2 - \sin \phi_1 \cos \phi_2 \cos \Delta \lambda\right)$$

- **Turn Rate (ROT):** Computes shortest angular distance across circular boundary:
  $$\Delta \text{COG} = \min(|\text{COG}_2 - \text{COG}_1|, 360 - |\text{COG}_2 - \text{COG}_1|)$$
  $$\text{ROT} = \frac{\Delta \text{COG}}{\Delta t} \times 60 \quad (\text{deg/min})$$

- **Acceleration:**
  $$a = \frac{v_2 - v_1}{\Delta t} \quad (\text{m/s}^2)$$

---

## 3. Trajectory Simplification (Ramer-Douglas-Peucker)

For web visualization, transmitting millions of raw vertices causes browser memory pressure. The platform applies the recursive **Ramer-Douglas-Peucker (RDP)** algorithm with a configurable spatial tolerance ($\epsilon = 0.0005^{\circ} \approx 50\text{m}$). Collinear points are simplified while preserving key turns, stops, and course changes.

---

## 4. Short-Gap Interpolation Policy

- **Defensible Window:** Gaps between 2 minutes and 10 minutes can be linearly interpolated with a 60-second resolution.
- **Uncertainty Tagging:** All interpolated coordinates have `is_interpolated=True`.
- **Long Gaps:** Never interpolated.
