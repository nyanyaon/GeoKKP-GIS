"""
/***************************************************************************
Adopted from a Geocoding & Reverse Geocoding script (2008) 
by ItOpen (info@itopen.it)
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import sys, os, json
from modules.utils import logMessage
from qgis.core import QgsSettings, QgsMessageLog


from .api import NetworkAccessManager, DEFAULT_MAX_REDIRECTS

NAM = NetworkAccessManager()

class OsmGeoCoder():
    url = 'https://nominatim.openstreetmap.org/search?format=json&q={address}'
    reverse_url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}'

    def geocode(self, address):
        try: 
            url = self.url.format(**{'address': address.decode('utf8')})
            logMessage(url)
            results = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))
            return [(rec['display_name'], (rec['lon'], rec['lat'])) for rec in results]
        except Exception as e:
            raise logMessage(str(e))

    def reverse(self, lon, lat):
        """single result"""
        try: 
            url = self.reverse_url.format(**{'lon': lon, 'lat': lat})
            logMessage(url)
            rec = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))
            return [(rec['display_name'], (rec['lon'], rec['lat']))]
        except Exception as e:
            raise logMessage(str(e))