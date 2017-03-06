
def get_param_xml(soup, name):
    param = soup.find("param", {"name": name})
    value = param["val"]


    if not param.has_attr("type"):
        return float(value)

    type_ = param["type"]

    if type_ == "string":
        return str(value)
    elif type_ == "bool":
        if value == "true":
            return True
        else:
            return False
    elif type_ == "float":
        return float(value)
    elif type_ == "int":
        return int(value)
    else:
        raise Exception("Invalid type %s"%(type_))
