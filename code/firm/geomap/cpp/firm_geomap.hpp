// firm.geomap (C++20): Vincenty's inverse geodesic on the WGS-84 ellipsoid (One Quant Book 14, chapter 10), the same
// iteration and series as the Python reference firm_geomap.py.
#pragma once
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace firm::geomap {

inline constexpr double kA = 6378137.0;
inline constexpr double kF = 1.0 / 298.257223563;
inline constexpr double kB = kA * (1.0 - kF);
inline constexpr double kC0 = 299792458.0;

inline double rad(double d) { return d * std::numbers::pi / 180.0; }

inline double geodesic_m(double lat1, double lon1, double lat2, double lon2) {
    if (lat1 == lat2 && lon1 == lon2) return 0.0;
    const double L = rad(lon2 - lon1);
    const double U1 = std::atan((1 - kF) * std::tan(rad(lat1))), U2 = std::atan((1 - kF) * std::tan(rad(lat2)));
    const double sinU1 = std::sin(U1), cosU1 = std::cos(U1), sinU2 = std::sin(U2), cosU2 = std::cos(U2);
    double lam = L, sin_s = 0, cos_s = 0, sigma = 0, cos2a = 0, cos2sm = 0;
    int it = 0;
    for (; it < 200; ++it) {
        const double sl = std::sin(lam), cl = std::cos(lam);
        sin_s = std::hypot(cosU2 * sl, cosU1 * sinU2 - sinU1 * cosU2 * cl);
        cos_s = sinU1 * sinU2 + cosU1 * cosU2 * cl;
        sigma = std::atan2(sin_s, cos_s);
        const double sin_a = cosU1 * cosU2 * sl / sin_s;
        cos2a = 1 - sin_a * sin_a;
        cos2sm = cos2a != 0 ? cos_s - 2 * sinU1 * sinU2 / cos2a : 0.0;
        const double C = kF / 16 * cos2a * (4 + kF * (4 - 3 * cos2a));
        const double prev = lam;
        lam = L + (1 - C) * kF * sin_a * (sigma + C * sin_s * (cos2sm + C * cos_s * (-1 + 2 * cos2sm * cos2sm)));
        if (std::fabs(lam - prev) < 1e-12) break;
    }
    if (it == 200) throw std::runtime_error("Vincenty inverse did not converge");
    const double u2 = cos2a * (kA * kA - kB * kB) / (kB * kB);
    const double A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)));
    const double B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)));
    const double ds = B * sin_s * (cos2sm + B / 4 * (cos_s * (-1 + 2 * cos2sm * cos2sm)
                                                       - B / 6 * cos2sm * (-3 + 4 * sin_s * sin_s) *
                                                             (-3 + 4 * cos2sm * cos2sm)));
    return kB * A * (sigma - ds);
}

// one-way time in microseconds over d metres in a medium of (group) index n
inline double floor_us(double d_m, double n = 1.0) { return d_m * n / kC0 * 1e6; }

}  // namespace firm::geomap
