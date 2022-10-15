import csv
import requests
import subprocess
import sys
import time
import urllib
from clint.textui import progress
import re
import base64

from classes.utils import Utils
import os 
os.getcwd() 


cr = None
MISSING = object()
nicely_formatted_csv_data_pattern = "{:<20} {:<20} {:<10} {:<10} {:<10} {:<40} {:<10}"

class VPNGateApp:
    """App class for VPN Gate"""

    def __init__(self, URL):
        self.URL = URL
        #super(VPNGate, self).__init__()
        return
 

    def write_openvpn_file(self,b64ovpndata, vpnname):
        openvpnconfigpath = ".vpnconfigs/vpnconfig_{0}.ovpn".format(vpnname)
        
        base64_bytes = b64ovpndata.encode("ascii")
        decoded_bytes = base64.b64decode(base64_bytes)
        decoded_ovpndata = decoded_bytes.decode("ascii")

        Utils.create_directory_path(openvpnconfigpath)

        fh = open(openvpnconfigpath, "w")
        fh.write(decoded_ovpndata)
        fh.write('\nscript-security 2\nup /etc/openvpn/update-resolv-conf\ndown /etc/openvpn/update-resolv-conf')
        fh.close()

        #print decoded_ovpndata
        return self.grab_ovpn_values(openvpnconfigpath)


    def grab_ovpn_values(self,openvpnconfigpath):

        protocol = None
        address_and_port = None
        address = None
        port = None

        for line in open(openvpnconfigpath, 'r'):

            if protocol == None:
                pattern = re.compile("^proto (tcp|udp)$") #tcp or udp?
                match = pattern.match(line)

                if match:
                    print ("found: " + match.group(1))
                    protocol = match.group(1)
                else:
                    # print('protocol not found')
                    pass

            if address_and_port == None:
                pattern2 = re.compile("^remote ([0-9\.]*) ([0-9]*)$") #ip address and port
                match2 = pattern2.match(line)

                if match2:
                    print ("found: " + match2.group(1) + " " + match2.group(2) )
                    address_and_port = match2
                    address  = match2.group(1)
                    port     = match2.group(2)
                else:
                   pass

        return protocol, address, port


    def run_ovpn_config(self, path):
        x = subprocess.Popen(['sudo', 'openvpn', '--config', path])
        try:
            while True:
                time.sleep(600)
            Utils.send_message("VPN connection established","now connected")
            # termination with Ctrl+C
        except:
            try:
                x.kill()
            except:
                pass
            while x.poll() != 0:
                time.sleep(1)
            print ('\nVPN terminated')
            Utils.send_message("vpn terminated","the vpn is now gone")
        return


    def grab_csv(self):
        print ("grabbing VPNGate CSV from : {0}, this may take a minute...".format(self.URL))
        print ("ctrl+c if you already have a cached list")
 
        try:
            with requests.Session() as session:
                r = session.get(self.URL, stream=True, hooks=dict(response=self.grab_csv_callback))
                data = r.text
                data = data.split("\n")
                print("length:", len(data))

                # headers = data[1].split(",")
                # headers[0] = headers[0].slice(1)
                # # a = headers[-1]
                # headers[-1] = headers[-1].split("\r")[0]


                data = data[1:-2]
                # print("r: ", r.text)
                csvdatapath = "vpndata.csv"
                # fh = open(csvdatapath, "wb")
                # fh.write(data)
                # fh.close()
                print("header:", data[0])

                f = open(csvdatapath, 'w')
                w = csv.writer(f, delimiter = ',')
                w.writerows([x.split(',') for x in data])
                f.close()
                # it seems that the requests module had a bug, or didn't support content-length headers /
                # in the response, so here we use urllib to do a HEAD request prior to download 
                # request2 = urllib.Request(self.URL)
                # request2.get_method = lambda : 'HEAD'
                # response2 = urllib.urlopen(request2) 
                # total_length = int(response2.info()['Content-Length'])
                # print("total length: ", total_length)
                # Utils.create_directory_path(csvdatapath)
                # with open(csvdatapath, 'wb') as f:
                #     for chunk in progress.bar(r.iter_content(chunk_size=1024) + 1): 
                #         if chunk:
                #             f.write(chunk)
                #             f.flush()
        except Exception as e:
            print(e)
            print ("[!ERROR] There was a problem fetching the data from vpngate.net\r\n")
        return

    def grab_csv_callback(self, r, *args, **kwargs):
        print ("data returned from {url}".format(url=r.url))

        # playing with callbacks 
        # csvdatapath = "vpndata.csv"
        # decoded_content = r.content.decode('utf-8')
        # print("decoded_content: ", decoded_content)
        # fh = open(csvdatapath, "wb")
        # fh.write(decoded_content)
        # fh.close()
        return r


    def grab_vpndata(self, chosenVPNName):
        file_handle.seek(0)
        for utf8_row in cr:
            if(chosenVPNName == utf8_row[0]):
                return utf8_row[14]
        return None


    def parse_csv(self, chosenCountryShortCodeArg=MISSING):
        global cr, MISSING, file_handle
        file_handle = open("vpndata.csv", "r")
        cr = csv.reader(file_handle, delimiter=',')

        for utf8_row in cr:
            (a) = utf8_row[:-1]
            if len(a) != 0:
                if chosenCountryShortCodeArg is MISSING:
                     print(nicely_formatted_csv_data_pattern.format(*a))
                else:
                    if a[6] == chosenCountryShortCodeArg:
                        print(nicely_formatted_csv_data_pattern.format(*a))
        return


