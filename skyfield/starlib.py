"""Python classes that represent various classes of star."""

from numpy import array, cos, sin, sqrt
from .constants import AU_KM, ASEC2RAD, DEG2RAD, C, C_AUDAY, T0
from .coordinates import GCRS
from .relativity import light_time_difference


class Star(object):

    def __init__(self, ra, dec,
                 pm_ra=0.0, pm_dec=0.0, parallax=0.0, radial_velocity=0.0):
        self.ra = ra
        self.dec = dec
        self.pm_ra = pm_ra
        self.pm_dec = pm_dec
        self.parallax = parallax
        self.radial_velocity = radial_velocity

        self._compute_vectors()

    def observe_from(self, observer):
        position, velocity = self._position, self._velocity
        jd = observer.jd
        dt = light_time_difference(position, observer.position)
        position = position + velocity * (T0 - jd.tdb - dt)
        vector = position - observer.position
        distance = sqrt((vector * vector).sum(axis=0))
        lighttime = distance / C_AUDAY

        g = GCRS(vector, velocity - observer.velocity, jd)
        g.observer = observer
        g.distance = distance
        g.lighttime = lighttime
        return g

    def _compute_vectors(self):
        """Compute the star's position as an ICRS position and velocity."""

        # Use 1 gigaparsec for stars whose parallax is zero.

        parallax = self.parallax
        if parallax <= 0.0:
            parallax = 1.0e-6

        # Convert right ascension, declination, and parallax to position
        # vector in equatorial system with units of AU.

        dist = 1.0 / sin(parallax * 1.0e-3 * ASEC2RAD)
        r = self.ra * 15.0 * DEG2RAD
        d = self.dec * DEG2RAD
        cra = cos(r)
        sra = sin(r)
        cdc = cos(d)
        sdc = sin(d)

        self._position = array((
            dist * cdc * cra,
            dist * cdc * sra,
            dist * sdc,
            )).reshape((3, 1))

        # Compute Doppler factor, which accounts for change in light
        # travel time to star.

        k = 1.0 / (1.0 - self.radial_velocity / C * 1000.0)

        # Convert proper motion and radial velocity to orthogonal
        # components of motion with units of AU/Day.

        pmr = self.pm_ra / (parallax * 365.25) * k
        pmd = self.pm_dec / (parallax * 365.25) * k
        rvl = self.radial_velocity * 86400.0 / AU_KM * k

        # Transform motion vector to equatorial system.

        self._velocity = array((
            - pmr * sra - pmd * sdc * cra + rvl * cdc * cra,
              pmr * cra - pmd * sdc * sra + rvl * cdc * sra,
              pmd * cdc + rvl * sdc,
              )).reshape((3, 1))
