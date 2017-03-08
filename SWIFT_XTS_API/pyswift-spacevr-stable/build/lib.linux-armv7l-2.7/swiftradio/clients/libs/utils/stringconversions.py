# -*- coding: utf-8 -*-
"""
simple functions for identifying and converting numerical values within a string 
"""
__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__company__ = "Tethers Unlimited, Inc."
__date__ = "Late Updated: 9/3/14"

def strval_numtype(s):
    """
    Description:    
    Parameters:     
    Return:         
    """         
    try:
        # note: hex must be in '0x____' format
        if s[:2] == "0x":
            s = s[2:]
            try:
                s.decode("hex")
                return 'hex'
            except (TypeError, ValueError):
                pass
    except (TypeError, ValueError):
        pass        

    try:
        int(s)
        return 'int'
    except (TypeError, ValueError):
        pass

    try:
        float(s)
        return 'float'
    except (TypeError, ValueError):
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return 'uint'
    except (TypeError, ValueError):
        pass        

    return 'unknown'    

def determine_datatype_from_text(s):
    """
    Description:    
    Parameters:     
    Return:         
    """         
    try:
        # note: hex must be in '0x____' format
        if s[:2] == "0x":
            # zero pad this string if hex value is of odd length
            if (len(s) % 2) != 0:
				s = "0x0" + s[2:] 
            s = s[2:]
            try:
                s.decode("hex")
                return 'hex'
            except (TypeError, ValueError):
                pass
    except (TypeError, ValueError):
        pass        

    try:
        int(s)
        return 'int'
    except (TypeError, ValueError):
        if "e" in s:            # allow BASEeEXP syntax (i.e. 1315e6) for ints... 
            if "." not in s:    # but only if BASE is not a float!
                try:
                    int(float(s))   # check that syntax is correct.
                    return 'int'
                except (TypeError, ValueError):
                    pass            
    try:
        float(s)
        return 'float'
    except (TypeError, ValueError):
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return 'uint'
    except (TypeError, ValueError):
        pass        

    return 'string'     

def return_num(s):
    """
    Description:    
    Parameters:     
    Return:         
    """     
    # hex Formated Strings ()
    num_type = determine_datatype_from_text(s)
    
    if num_type == 'int':
        return int(float(s))
    elif num_type == 'uint':
        return int(float(s))    
    elif num_type == 'float':
        return float(s)
    elif num_type == 'hex':
        # note: hex must be in '0x____' format
        # zero pad this string if hex value is of odd length
        if (len(s) % 2) != 0:
            s = "0x0" + s[2:]
        s = s[2:]
        return s.decode("hex")     
    else:
        return None

def is_number(s):
    """
    Description:    
    Parameters:     
    Return:         
    """
    numtype = determine_datatype_from_text(s)         
    if numtype == 'string':
        return False
    else:
        return True

if __name__ == '__main__':
    nums = ["2134", "21s12", "3122131234", "asdasd", "two", "-1", "-1023", '2.3', '-2.3']
    
    for num in nums:
        print num
        print is_number(str(num))
        print strval_numtype(str(num))
        print return_num(str(num))
        print ""    

    raw_input("press enter to continue...")