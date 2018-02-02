"""
Functions: geo2grid, grid2geo, geo2gridio, grid2geoio

geo2grid:
    input: Latitude and Longitude in Decimal Degrees.

    output: Zone, Easting and Northing of a point in metres.
    (Default projection is Universal Transverse Mercator.)

grid2geo:
    input: Zone, Easting and Northing of a point in metres.
    (Default projection is Universal Transverse Mercator.)

    output: Latitude and Longitude in Decimal Degrees.

xyz2llh:
    Input: Cartesian XYZ coordinate in metres.

    Output: Latitude and Longitude in Decimal.
    Degrees and Ellipsoidal Height in Metres.

geo2gridio:
    No Input:
    Prompts the user for the name of a file in csv format. Data in the file
    must be in the form Point ID, Latitude, Longitude in Decimal Degrees with
    no header line.

    No Output:
    Uses the function geo2grid to convert each row in the csv file into a
    coordinate with UTM Zone, Easting (m), Northing (m). This data is written
    to a new file with the name <inputfile>_out.csv

grid2geoio:
    No Input:
    Prompts the user for the name of a file in csv format. Data in the file
    must be in the form Point ID, UTM Zone, Easting (m), Northing (m) with
    no header line.

    No Output:
    Uses the function grid2geo to convert each row in the csv file into a
    latitude and longitude in Degrees, Minutes and Seconds. This data is
    written to a new file with the name <inputfile>_out.csv

Ref: http://www.icsm.gov.au/gda/tech.html
Ref: http://www.mygeodesy.id.au/documents/Karney-Krueger%20equations.pdf
"""

# Author: Josh Batchelor <josh.batchelor@ga.gov.au>

from decimal import *
from math import sqrt, log, degrees, radians, sin, cos, tan, sinh, cosh, atan, atan2
import os
import csv
from constants import grs80
from conversions import dd2dms, dms2dd


getcontext().prec = 28
# Universal Transverse Mercator Projection Parameters
proj = grs80
# Ellipsoidal Constants
f = 1 / proj[1]
semi_maj = proj[0]
semi_min = float(semi_maj * (1 - f))
ecc1sq = float(f * (2 - f))
ecc2sq = float(ecc1sq/(1 - ecc1sq))
ecc1 = sqrt(ecc1sq)
n = f / (2 - f)
n = float(n)
n2 = n ** 2


# Rectifying Radius (Horner Form)
A = proj[0] / (1 + n) * ((n2 *
                          (n2 *
                           (n2 *
                            (25 * n2 + 64)
                            + 256)
                           + 4096)
                          + 16384)
                         / 16384.)

# Alpha Coefficients (Horner Form)
a2 = ((n *
       (n *
        (n *
         (n *
          (n *
           (n *
            ((37884525 - 75900428 * n)
             * n + 42422016)
            - 89611200)
           + 46287360)
          + 63504000)
         - 135475200)
        + 101606400))
      / 203212800.)

a4 = ((n2 *
       (n *
        (n *
         (n *
          (n *
           (n *
            (148003883 * n + 83274912)
            - 178508970)
           + 77690880)
          + 67374720)
         - 104509440)
        + 47174400))
      / 174182400.)

a6 = ((n ** 3 *
       (n *
        (n *
         (n *
          (n *
           (318729724 * n - 738126169)
           + 294981280)
          + 178924680)
         - 234938880)
        + 81164160))
      / 319334400.)

a8 = ((n ** 4 *
       (n *
        (n *
         ((14967552000 - 40176129013 * n) * n + 6971354016)
         - 8165836800)
        + 2355138720))
      / 7664025600.)

a10 = ((n ** 5 *
        (n *
         (n *
          (10421654396 * n + 3997835751)
          - 4266773472)
         + 1072709352))
       / 2490808320.)

a12 = ((n ** 6 *
        (n *
         (175214326799 * n - 171950693600)
         + 38652967262))
       / 58118860800.)

a14 = ((n ** 7 *
        (13700311101 - 67039739596 * n))
       / 12454041600.)

a16 = (1424729850961 * n ** 8) / 743921418240.

# Beta Coefficients (Horner Form)
b2 = ((n *
       (n *
        (n *
         (n *
          (n *
           (n *
            ((37845269 - 31777436 * n) - 43097152)
            + 42865200)
           + 752640)
          - 104428800)
         + 180633600)
        - 135475200))
      / 270950400.)

b4 = ((n ** 2 *
       (n *
        (n *
         (n *
          (n *
           ((-24749483 * n - 14930208) * n + 100683990)
           - 152616960)
          + 105719040)
         - 23224320)
        - 7257600))
      / 348364800.)

b6 = ((n ** 3 *
       (n *
        (n *
         (n *
          (n *
           (232468668 * n - 101880889)
           - 39205760)
          + 29795040)
         + 28131840)
        - 22619520))
      / 638668800.)

b8 = ((n ** 4 *
       (n *
        (n *
         ((-324154477 * n - 1433121792) * n + 876745056)
         + 167270400)
        - 208945440))
      / 7664025600.)

b10 = ((n ** 5 *
        (n *
         (n *
          (312227409 - 457888660 * n)
          + 67920528)
         - 70779852))
       / 2490808320.)

b12 = ((n ** 6 *
        (n *
         (19841813847 * n + 3665348512)
         - 3758062126))
       / 116237721600.)

b14 = ((n ** 7 *
        (1989295244 * n - 1979471673))
       / 49816166400.)

b16 = ((-191773887257 * n ** 8) / 3719607091200.)


def geo2grid(lat, long):
    """
    input: Latitude and Longitude in Decimal Degrees.

    output: Zone, Easting and Northing of a point in metres.
    (Default projection is Universal Transverse Mercator.)
    """
    # Calculate Zone
    zone = int((float(long) - (proj[6] - (1.5 * proj[5]))) / proj[5])
    centmeridian = float(zone * proj[5]) + (proj[6] - proj[5])
    # Conformal Latitude
    sigx = (ecc1 * tan(radians(lat))) / sqrt(1 + (tan(radians(lat)) ** 2))
    sig = sinh(ecc1 * (0.5 * log((1 + sigx) / (1 - sigx))))
    conf_lat = tan(radians(lat)) * sqrt(1 + sig ** 2) - sig * sqrt(1 + (tan(radians(lat)) ** 2))
    conf_lat = atan(conf_lat)
    # Longitude Difference
    long_diff = radians(Decimal(long) - Decimal(str(centmeridian)))
    # Gauss-Schreiber Ratios
    xi1 = atan(tan(conf_lat) / cos(long_diff))
    eta1x = sin(long_diff) / (sqrt(tan(conf_lat) ** 2 + cos(long_diff) ** 2))
    eta1 = log(eta1x + sqrt(1 + eta1x ** 2))
    # Transverse Mercator Ratios
    eta2 = a2 * cos(2 * xi1) * sinh(2 * eta1)
    eta4 = a4 * cos(4 * xi1) * sinh(4 * eta1)
    eta6 = a6 * cos(6 * xi1) * sinh(6 * eta1)
    eta8 = a8 * cos(8 * xi1) * sinh(8 * eta1)
    eta10 = a10 * cos(10 * xi1) * sinh(10 * eta1)
    eta12 = a12 * cos(12 * xi1) * sinh(12 * eta1)
    eta14 = a14 * cos(14 * xi1) * sinh(14 * eta1)
    eta16 = a16 * cos(16 * xi1) * sinh(16 * eta1)
    xi2 = a2 * sin(2 * xi1) * cosh(2 * eta1)
    xi4 = a4 * sin(4 * xi1) * cosh(4 * eta1)
    xi6 = a6 * sin(6 * xi1) * cosh(6 * eta1)
    xi8 = a8 * sin(8 * xi1) * cosh(8 * eta1)
    xi10 = a10 * sin(10 * xi1) * cosh(10 * eta1)
    xi12 = a12 * sin(12 * xi1) * cosh(12 * eta1)
    xi14 = a14 * sin(14 * xi1) * cosh(14 * eta1)
    xi16 = a16 * sin(16 * xi1) * cosh(16 * eta1)
    eta = eta1 + eta2 + eta4 + eta6 + eta8 + eta10 + eta12 + eta14 + eta16
    xi = xi1 + xi2 + xi4 + xi6 + xi8 + xi10 + xi12 + xi14 + xi16
    # Transverse Mercator Co-ordinates
    x = A * eta
    y = A * xi
    # MGA Co-ordinates
    east = proj[4] * Decimal(str(x)) + proj[2]
    north = proj[4] * Decimal(str(y)) + proj[3]
    return zone, round(float(east), 5), round(float(north), 5)


def grid2geo(zone, easting, northing):
    """
    input: Zone, Easting and Northing of a point in metres.
    (Default projection is Universal Transverse Mercator.)

    output: Latitude and Longitude in Decimal Degrees.
    """
    # Transverse Mercator Co-ordinates
    x = (easting - float(proj[2])) / float(proj[4])
    y = (northing - float(proj[3])) / float(proj[4])
    # Transverse Mercator Ratios
    xi = y / A
    eta = x / A
    # Gauss-Schreiber Ratios
    xi2 = b2 * sin(2 * xi) * cosh(2 * eta)
    xi4 = b4 * sin(4 * xi) * cosh(4 * eta)
    xi6 = b6 * sin(6 * xi) * cosh(6 * eta)
    xi8 = b8 * sin(8 * xi) * cosh(8 * eta)
    xi10 = b10 * sin(10 * xi) * cosh(10 * eta)
    xi12 = b12 * sin(12 * xi) * cosh(12 * eta)
    xi14 = b14 * sin(14 * xi) * cosh(14 * eta)
    xi16 = b16 * sin(16 * xi) * cosh(16 * eta)
    eta2 = b2 * cos(2 * xi) * sinh(2 * eta)
    eta4 = b4 * cos(4 * xi) * sinh(4 * eta)
    eta6 = b6 * cos(6 * xi) * sinh(6 * eta)
    eta8 = b8 * cos(8 * xi) * sinh(8 * eta)
    eta10 = b10 * cos(10 * xi) * sinh(10 * eta)
    eta12 = b12 * cos(12 * xi) * sinh(12 * eta)
    eta14 = b14 * cos(14 * xi) * sinh(14 * eta)
    eta16 = b16 * cos(16 * xi) * sinh(16 * eta)
    xi1 = xi + xi2 + xi4 + xi6 + xi8 + xi10 + xi12 + xi14 + xi16
    eta1 = eta + eta2 + eta4 + eta6 + eta8 + eta10 + eta12 + eta14 + eta16
    # Conformal Latitude
    conf_lat = (sin(xi1)) / (sqrt((sinh(eta1)) ** 2 + (cos(xi1)) ** 2))
    t1 = conf_lat
    conf_lat = atan(conf_lat)

    # Finding t using Newtons Method
    def sigma(t):
        sigma = sinh(
            ecc1 * 0.5 * log((1 + ((ecc1 * t) / (sqrt(1 + t ** 2)))) / (1 - ((ecc1 * t) / (sqrt(1 + t ** 2))))))
        return sigma

    def ftn(t):
        ftn = t * sqrt(1 + (sigma(t)) ** 2) - sigma(t) * sqrt(1 + t ** 2) - t1
        return ftn

    def f1tn(t):
        f1tn = (sqrt(1 + (sigma(t)) ** 2) * sqrt(1 + t ** 2) - sigma(t) * t) * (
                ((1 - float(ecc1sq)) * sqrt(1 + t ** 2)) / (1 + (1 - float(ecc1sq)) * t ** 2))
        return f1tn

    t2 = t1 - (ftn(t1)) / (f1tn(t1))
    t3 = t2 - (ftn(t2)) / (f1tn(t2))
    t4 = t3 - (ftn(t3)) / (f1tn(t3))
    # Test No of Iterations Required (this will impact script performance)
    # t5 = t4 - (ftn(t4))/(f1tn(t4))
    # Compute Latitude
    lat = degrees(atan(t4))
    # Compute Longitude
    cm = float((zone * proj[5]) + proj[6] - proj[5])
    long_diff = degrees(atan(sinh(eta1) / cos(xi1)))
    long = cm + long_diff
    return round(lat, 11), round(long, 11)


def xyz2llh(x, y, z):
    """
    Input: Cartesian XYZ coordinate in metres

    Output: Latitude and Longitude in Decimal
    Degrees and Ellipsoidal Height in Metres
    """
    # Calculate Longitude
    long = atan2(y, x)
    # Calculate Latitude
    p = sqrt(x**2 + y**2)
    latinit = atan((z*(1+ecc2sq))/p)
    lat = latinit
    itercheck = 1
    while abs(itercheck) > 1e-10:
        nu = semi_maj/(sqrt(1 - ecc1sq * (sin(lat))**2))
        itercheck = lat - atan((z + nu * ecc1sq * sin(lat))/p)
        lat = atan((z + nu * ecc1sq * sin(lat))/p)
    nu = semi_maj/(sqrt(1 - ecc1sq * (sin(lat))**2))
    ellht = p/(cos(lat)) - nu
    # Convert Latitude and Longitude to Degrees
    lat = degrees(lat)
    long = degrees(long)
    return lat, long, ellht


def llh2xyz(lat, long, ellht):
    """
    Input: Latitude and Longitude in Decimal Degrees, Ellipsoidal Height in metres
    Output: Cartesian X, Y, Z Coordinates in metres
    """
    # Convert lat & long to radians
    lat = radians(lat)
    long = radians(long)
    # Calculate Ellipsoid Radius of Curvature in the Prime Vertical - nu
    if lat == 0:
        nu = proj[0]
    else:
        nu = semi_maj/(sqrt(1 - ecc1sq * (sin(lat)**2)))
    # Calculate x, y, z
    x = Decimal(str((nu + ellht) * cos(lat) * cos(long)))
    y = Decimal(str((nu + ellht) * cos(lat) * sin(long)))
    z = Decimal(str(((semi_min**2 / semi_maj**2) * nu + ellht) * sin(lat)))
    return x, y, z


def grid2geoio():
    """
    No Input:
    Prompts the user for the name of a file in csv format. Data in the file
    must be in the form Point ID, UTM Zone, Easting (m), Northing (m) with
    no header line.

    No Output:
    Uses the function grid2geo to convert each row in the csv file into a
    latitude and longitude in Degrees, Minutes and Seconds. This data is
    written to a new file with the name <inputfile>_out.csv
    """
    # Enter Filename
    print('Enter co-ordinate file (\.csv)\:')
    fn = input()
    # Open Filename
    csvfile = open(fn)
    csvreader = csv.reader(csvfile)
    # Create Output File
    fn_part = (os.path.splitext(fn))
    fn_out = fn_part[0] + '_out' + fn_part[1]
    outfile = open(fn_out, 'w')
    # Write Output
    outfilewriter = csv.writer(outfile)
    # outfilewriter.writerow(['Pt', 'Latitude', 'Longitude'])
    for row in csvreader:
        pt_num = row[0]
        zone = float(row[1])
        east = float(row[2])
        north = float(row[3])
        # Calculate Conversion
        lat, long = grid2geo(zone, east, north)
        lat = dd2dms(lat)
        long = dd2dms(long)
        output = [pt_num, lat, long]
        outfilewriter.writerow(output)
    # Close Files
    outfile.close()
    csvfile.close()


def geo2gridio():
    """
    No Input:
    Prompts the user for the name of a file in csv format. Data in the file
    must be in the form Point ID, Latitude, Longitude in Decimal Degrees with
    no header line.

    No Output:
    Uses the function geo2grid to convert each row in the csv file into a
    coordinate with UTM Zone, Easting (m), Northing (m). This data is written
    to a new file with the name <inputfile>_out.csv
    """
    # Enter Filename
    print('Enter co-ordinate file:')
    fn = input()
    # Open Filename
    csvfile = open(fn)
    csvreader = csv.reader(csvfile)
    # Create Output File
    fn_part = (os.path.splitext(fn))
    fn_out = fn_part[0] + '_out' + fn_part[1]
    outfile = open(fn_out, 'w')
    # Write Output
    outfilewriter = csv.writer(outfile)
    # outfilewriter.writerow(['Pt', 'Zone', 'Easting', 'Northing'])
    for row in csvreader:
        pt_num = row[0]
        lat = dms2dd(float(row[1]))
        long = dms2dd(float(row[2]))
        # Calculate Conversion
        output = geo2grid(lat, long)
        output = [pt_num] + list(output)
        outfilewriter.writerow(output)
    # Close Files
    outfile.close()
    csvfile.close()