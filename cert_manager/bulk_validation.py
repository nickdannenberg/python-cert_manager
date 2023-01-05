from validation import Validation
from DNS import dnslookup

class BulkValidationHelper:
    """Perform DCV for a number of domains.
    Currently only CNAME validation is implemented.
    """

    def __init__(self, client):
        self.dcv = Validation(client)
        self.__started = None

    def start_all(self, only_secondlevel=True, method='cname', **kwargs):
        """Initiate DCV for all domains with a specific matching some filter.

        If validation was started previously, this method will throw an Exception.

        :param bool only_secondlevel: filter out domains containing
                                      more than 1 dot. To get rid of wildcard domains,
                                      IPs and sub-domains. This is wrong for '.co.uk' and
                                      other TLDs.
        :param str method: DCV method
        :param dict kwargs: filter for searching. Defaults to  order_status='NOT_INITIATED',
                            dcv_status='NOT_VALIDATED'.

        :return list[dict]:  list of dicts with 'domain', and the result returned from `start`

        """

        if not(kwargs):
            kwargs = {'dcv_status':'NOT_VALIDATED', 'order_status':'NOT_INITIATED'}

        if only_secondlevel:
            ## FIXME this filters out IPs and "normal subdomains". But
            ## it's incorrect for .co.uk and others
            domains = [d['domain'] for d in self.find(**kwargs) if
                       d['domain'].count('.')==1]
        else:
            domains = [d['domain'] for d in self.find(**kwargs)]


        self.__started = [ self.start(d, method) | {'domain':d, 'method':method} for d in domains ]
        return self.__started

    def submit_started_cname(self, dcvs):
        """Submit previously initiated DCV via cname. But only if recorded CNAME challenges are visible in DNS

        :param dict dcvs: recorded DCV domains and challenge parameters.
        :return list: list of domains for which DCV was submitted.
        """


        submitted = []
        for dcv in dcvs:
            assert( dcv['method'] == 'cname')
            res = None
            try:
                res = dnslookup(dcv['host'], 'CNAME')
                res = res[0]
                if res[-1] == '.':
                    res = res[:-1]
            except:
                pass
            ptr = dcv['point']
            if ptr[-1] == '.':
                ptr = ptr[:-1]
            if not(res and res == dcv['point']):
                continue
            else:
                try:
                    self.dcv.submit(dcv['domain'],method='cname')
                except:
                    continue
                submitted.append(dcv['domain'])

        return submitted

    def submit_started(self):
        """Submit all previously started DCV requests.

        :return set: domains for which DCV requests were submitted
        """
        if not(self.__started):
            print('No previously started DCV requests found')
            return

        submitted = set()
        started = self.__started

        submitted.update( self.submit_started_cname([dcv for dcv in started if dcv['method']=='cname']))
        started = [dcv for dcv in started if not(dcv['domain'] in submitted)]

        # FIXME: implement other DCV methods
        # submitted.update(self.submit_started_email([dcv for dcv in started if dcv['method']=='email']))
        # started = [dcv for dcv in started if not(dcv['domain'] in submitted_email)]
        #
        # submitted.update(self.submit_started_http([dcv for dcv in started if dcv['method']=='http']))
        # started = [dcv for dcv in started if not(dcv['domain'] in submitted_http)]
        #
        # submitted.update( self.submit_started_https([dcv for dcv in started if dcv['method']=='https']))
        # started = [dcv for dcv in started if not(dcv['domain'] in submitted_https)]

        self.__started = started
        return submitted

    def print_started(self):
        """Print pending DCV challenges"""
        # FIXME: what should be printed for DCV methods email, http(s)?

        for dcv in self.__started:
            if dcv['method'] == 'cname':
                print(f"{dcv['host']} IN CNAME {dcv['point']}")
