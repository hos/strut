
def get_value_xml(soup, name):
    return float(soup.find("value", {"name": name})["v"])
