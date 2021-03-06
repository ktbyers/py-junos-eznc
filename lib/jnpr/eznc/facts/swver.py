import re

class version_info(object):  
  def __init__(self, verstr ):
    """verstr - version string"""
    m1 = re.match('(.*)([RBIXS])(.*)', verstr)
    self.type = m1.group(2)
    self.major = tuple(map(int,m1.group(1).split('.'))) # creates tuyple
    after_type = m1.group(3).split('.')
    self.minor = after_type[0]
    if 'X' == self.type:
      # assumes form similar to "45-D10", so extract the bits from this
      xm = re.match("(\d+)-(\w)(.*)", self.minor)
      self.minor = tuple([int(xm.group(1)), xm.group(2), int(xm.group(3))])
      if len(after_type) < 2:
        self.build = None
      else:
        self.build = int(after_type[1])
    elif 'I' == self.type:
      self.build = after_type[1]        # assumes that we have a build/spin, but not numeric
    else:
      self.build = int(after_type[1])   # assumes numeric build/spin

    self.as_tuple = self.major + tuple([self.minor, self.build])

  def __repr__(self):
    retstr = "junos.versino_info(major={major}, type={type}, minor={minor}, build={build})".format(
      major=self.major,
      type=self.type,
      minor=self.minor,
      build=self.build
    )
    return retstr

  def _cmp_tuple(self,other):
    if self.type == 'I': raise RuntimeError("Internal Build")
    bylen = {
      2: (self.as_tuple[0:2]),
      4: self.as_tuple
    }
    return bylen[len(other)]

  def __lt__(self,other): return self._cmp_tuple(other) < other
  def __le__(self,other): return self._cmp_tuple(other) <= other
  def __gt__(self,other): return self._cmp_tuple(other) > other
  def __ge__(self,other): return self._cmp_tuple(other) >= other
  def __eq__(self,other): return self._cmp_tuple(other) == other  
  def __ne__(self,other): return self._cmp_tuple(other) != other

def software_version(junos, facts):
  
  f_persona = facts.get('personality')
  f_master = facts.get('master')
      
  if f_persona == 'MX':
    x_swver = junos.cli("show version invoke-on all-routing-engines", format='xml')

  elif f_persona == 'SWITCH':
    ## most EX switches support the virtual-chassis feature, so the 'all-members' option would be valid
    ## in some products, this options is not valid (i.e. not vc-capable. so we're going to try for vc, and if that
    ## throws an exception we'll rever to non-VC
    try:
      x_swver = junos.rpc.cli("show version all-members", format='xml')
    except:
      facts['vc_capable'] = False
      x_swver = junos.rpc.cli("show version", format='xml')
    else:
      facts['vc_capable'] = True
  else:
    x_swver = junos.rpc.cli("show version",format='xml')
  
  if x_swver[0].tag == 'multi-routing-engine-results':
    raise RuntimeError("Multi-RE platform found -- IMPLEMENT ME!")
    # swver_infos = swver.xpath('//software-information')
    # swver_infos.each do |re_sw|
    #   re_name = re_sw.xpath('preceding-sibling::re-name').text.upcase
    #   re_sw.xpath('package-information[1]/comment').text =~ /\[(.*)\]/
    #   ver_key = ('version_' + re_name).to_sym
    #   facts[ver_key] = $1
    # end
    # master_id = f_master
    # facts[:version] =
    #   facts[("version_" + "RE" + master_id).to_sym] ||
    #   facts[('version_' + "FPC" + master_id).to_sym]
  else:
    pkginfo = x_swver.xpath('.//package-information[name = "junos"]/comment')[0].text    
    facts['version'] = re.findall(r'\[(.*)\]', pkginfo)[0]

  facts['version_info'] = version_info(facts['version'])
