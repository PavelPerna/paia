# ai/singleton.py

class PAIASingleton(object):
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(PAIASingleton, cls).__new__(cls)
    return cls.instance