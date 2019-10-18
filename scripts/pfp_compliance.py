# standard modules
import copy
import logging
import os
import platform
import traceback
# 3rd party modules
import timezonefinder
# PFP modules
import pfp_gui
import pfp_io
import pfp_utils

logger = logging.getLogger("pfp_log")

def change_variable_names(cfg, ds):
    """
    Purpose:
     Change variable names to the new (October 2018) scheme.
    Usage:
    Author: PRI
    Date: October 2018
    """
    # get a list of potential mappings
    rename_list = [v for v in list(cfg["Variables"].keys()) if "rename" in cfg["Variables"][v]]
    # loop over the variables in the data structure
    series_list = list(ds.series.keys())
    for label in series_list:
        if label in rename_list:
            new_name = cfg["Variables"][label]["rename"]
            ds.series[new_name] = ds.series.pop(label)
    return

def check_executables():
    # check for the executable files required
    if platform.system() == "Windows":
        executable_extension = ".exe"
    else:
        executable_extension = ""
    executable_names = ["solo/bin/sofm", "solo/bin/solo", "solo/bin/seqsolo",
                        "mds/bin/gf_mds", "mpt/bin/ustar_mp"]
    missing_executable = False
    for executable_name in executable_names:
        executable_name = executable_name + executable_extension
        if not os.path.isfile(executable_name):
            missing_executable = True
    if missing_executable:
        msg = "One or more of the required executable files could not be found.\n"
        msg = msg + "If you are running on Windows, clone the repository again.\n"
        msg = msg + "If you are running on OSX or Linux, use the make_nix script\n"
        msg = msg + "to compile the executables."
        result = pfp_gui.MsgBox_Quit(msg, title="Critical")
    return

def check_l4_controlfile(cf):
    """
    Purpose:
     Parse the L4 control file to make sure the syntax is correct and that the
     control file contains all of the information needed.
    Usage:
     result = pfp_compliance.check_l4_controlfile(cf)
     where cf is a ConfigObj object
           result is True if the L4 control file is compliant
                     False if it is not compliant
    Side effects:
    Author: PRI
    Date: September 2019
    """
    # initialise the return logical
    ok = True
    try:
        for key1 in cf:
            if key1 in ["Files", "Global", "Options"]:
                for key2 in cf[key1]:
                    value = cf[key1][key2]
                    if ("browse" not in value):
                        value = strip_characters_from_string(value, ['"', "'"])
            elif key1 in ["Drivers"]:
                for key2 in cf[key1]:
                    for key3 in cf[key1][key2]:
                        if key3 in ["GapFillFromAlternate", "GapFillFromClimatology"]:
                            for key4 in cf[key1][key2][key3]:
                                for key5 in cf[key1][key2][key3][key4]:
                                    cf[key1][key2][key3][key4].rename(key5, key5.lower())
                                    value = cf[key1][key2][key3][key4][key5.lower()]
                                    value = strip_characters_from_string(value, ['"', "'"])
                        elif key3 in ["MergeSeries", "RangeCheck", "ExcludeDates"]:
                            # strip out unwanted characters
                            for key4 in cf[key1][key2][key3]:
                                # force lower case
                                cf[key1][key2][key3].rename(key4, key4.lower())
                                value = cf[key1][key2][key3][key4.lower()]
                                value = strip_characters_qc_checks(key3, value)
        logger.info(" Saving " + cf.filename)
        cf.write()
    except Exception:
        ok = False
        msg = " An error occurred while parsing the L4 control file"
        logger.error(msg)
        error_message = traceback.format_exc()
        logger.error(error_message)
    return ok

def check_l6_controlfile(cf):
    """
    Purpose:
     Check a control file to see if it conforms to the the syntax expected at L6.
    Usage:
    Side effects:
    Author: PRI
    Date: August 2019
    """
    ok = True
    # check to see if we have an old style L6 control file
    if "ER" in cf.keys() or "NEE" in cf.keys() or "GPP" in cf.keys():
        ok = False
        msg = "This is an old version of the L6 control file.\n"
        msg = msg + "Close the L6 control file and create a new one from\n"
        msg = msg + "the template in PyFluxPro/controlfiles/template/L6."
        result = pfp_gui.MsgBox_Quit(msg, title="Critical")
        return ok
    try:
        for key1 in cf:
            if key1 in ["Files", "Global", "Options"]:
                for key2 in cf[key1]:
                    value = cf[key1][key2]
                    if ("browse" not in value):
                        value = strip_characters_from_string(value, ['"', "'"])
            elif key1 in ["EcosystemRespiration"]:
                for key2 in cf[key1]:
                    for key3 in cf[key1][key2]:
                        if key3 in ["ERUsingSOLO", "ERUsingLloydTaylor", "ERUsingLasslop"]:
                            for key4 in cf[key1][key2][key3]:
                                for key5 in cf[key1][key2][key3][key4]:
                                    cf[key1][key2][key3][key4].rename(key5, key5.lower())
                                    value = cf[key1][key2][key3][key4][key5]
                                    value = strip_characters_from_string(value, ['"', "'"])
                        elif key3 in ["MergeSeries"]:
                            # strip out unwanted characters
                            for key4 in cf[key1][key2][key3]:
                                # force lower case
                                cf[key1][key2][key3].rename(key4, key4.lower())
                                value = cf[key1][key2][key3][key4.lower()]
                                value = strip_characters_from_string(value, [" ", '"', "'"])
            elif key1 in ["NetEcosystemExchange", "GrossPrimaryProductivity"]:
                for key2 in cf[key1]:
                    for key3 in cf[key1][key2]:
                        value = cf[key1][key2][key3]
                        value = strip_characters_from_string(value, ['"', "'"])
        logger.info(" Saving " + cf.filename)
        cf.write()
    except Exception:
        ok = False
        msg = " An error occurred while parsing the L6 control file"
        logger.error(msg)
        error_message = traceback.format_exc()
        logger.error(error_message)
    return ok

def copy_ws_wd(ds):
    """
    Purpose:
     Make sure the Ws and Wd variables are in the L3 netCDF files.
    Usage:
    Author: PRI
    Date: October 2018
    """
    # get a list of the series
    series_list = sorted(list(ds.series.keys()))
    if "Wd" not in series_list:
        if "Wd_SONIC_Av" in series_list:
            ds.series["Wd"] = copy.deepcopy(ds.series["Wd_SONIC_Av"])
            ds.series["Wd"]["Attr"]["long_name"] = "Wind direction (copied from Wd_SONIC_Av)"
    if "Ws" not in series_list:
        if "Ws_SONIC_Av" in series_list:
            ds.series["Ws"] = copy.deepcopy(ds.series["Ws_SONIC_Av"])
            ds.series["Ws"]["Attr"]["long_name"] = "Wind speed (copied from Ws_SONIC_Av)"
    return

def ParseConcatenateControlFile(cf):
    """
    Purpose:
     Make the concatenate information dictionary
    Usage:
    Side effects:
    Author: PRI
    Date: August 2019
    """
    cc_info = {}
    # add key for suppressing output of intermediate variables e.g. Cpd etc
    opt = pfp_utils.get_keyvaluefromcf(cf, ["Options"], "KeepIntermediateSeries", default="No")
    cc_info["RemoveIntermediateSeries"] = {"KeepIntermediateSeries": opt, "not_output": []}
    return cc_info

def ParseL3ControlFile(cf, ds):
    """
    Purpose:
     Parse the L3 control file and return contents in the l3_info dictionary.
    Usage:
    Side effects:
    Author: PRI
    Date: August 2019
    """
    ds.returncodes["message"] = "OK"
    ds.returncodes["value"] = 0
    l3_info = {}
    # add key for suppressing output of intermediate variables e.g. Cpd etc
    opt = pfp_utils.get_keyvaluefromcf(cf, ["Options"], "KeepIntermediateSeries", default="No")
    l3_info["RemoveIntermediateSeries"] = {"KeepIntermediateSeries": opt, "not_output": []}
    return l3_info

def strip_characters_from_string(v, strip_list):
    """ Parse key values to remove unnecessary characters."""
    for c in strip_list:
        if c in v:
            v = v.replace(c, "")
    return v

def strip_characters_qc_checks(k, v):
    """ Parse value from control file to remove unnecessary characters."""
    try:
        # check to see if it is a number
        r = float(v)
    except ValueError as e:
        if ("[" in v) and ("]" in v) and ("*" in v):
            # old style of [value]*12
            v = v[v.index("[")+1:v.index("]")]
        elif ("[" in v) and ("]" in v) and ("*" not in v):
            # old style of [1,2,3,4,5,6,7,8,9,10,11,12]
            v = v.replace("[", "").replace("]", "")
    # remove white space and quotes
    if k in ["RangeCheck", "DiurnalCheck", "DependencyCheck",
             "MergeSeries", "AverageSeries"]:
        strip_list = [" ", '"', "'"]
    elif k in ["ExcludeDates", "ExcludeHours"]:
        # don't remove white space between date and time
        strip_list = ['"', "'"]
    strip_characters_from_string(v, strip_list)
    return v

def remove_variables(cfg, ds):
    """
    Purpose:
     Remove deprecated variables from a netCDF file.
    Usage:
    Author: PRI
    Date: October 2018
    """
    remove_list = [v for v in list(cfg["Variables"].keys()) if "remove" in cfg["Variables"][v]]
    series_list = sorted(list(ds.series.keys()))
    for label in series_list:
        if label in remove_list:
            ds.series.pop(label)
    return

def change_global_attributes(cfg, ds):
    """
    Purpose:
     Clean up the global attributes.
    Usage:
    Author: PRI
    Date: October 2018
    """
    # check site_name is in ds.globalattributes
    gattr_list = list(ds.globalattributes.keys())
    if "site_name" not in gattr_list:
        logger.warning("Globel attributes: site_name not found")
    # check latitude and longitude are in ds.globalattributes
    if "latitude" not in gattr_list:
        logger.warning("Global attributes: latitude not found")
    else:
        lat_string = str(ds.globalattributes["latitude"])
        if len(lat_string) == 0:
            logger.warning("Global attributes: latitude empty")
        else:
            lat = pfp_utils.convert_anglestring(lat_string)
        ds.globalattributes["latitude"] = str(lat)
    if "longitude" not in gattr_list:
        logger.warning("Global attributes: longitude not found")
    else:
        lon_string = str(ds.globalattributes["longitude"])
        if len(lon_string) == 0:
            logger.warning("Global attributes: longitude empty")
        else:
            lon = pfp_utils.convert_anglestring(lon_string)
        ds.globalattributes["longitude"] = str(lon)
    # check to see if there there is a time_zone global attribute
    gattr_list = list(ds.globalattributes.keys())
    if not "time_zone" in gattr_list:
        # get the site name
        site_name = ds.globalattributes["site_name"]
        sn = site_name.replace(" ","").replace(",","").lower()
        # first, see if the site is in constants.tz_dict
        if sn in list(c.tz_dict.keys()):
            ds.globalattributes["time_zone"] = c.tz_dict[sn]
        else:
            if "latitude" in gattr_list and "longitude" in gattr_list:
                lat = float(ds.globalattributes["latitude"])
                lon = float(ds.globalattributes["longitude"])
                if lat != -9999 and lon != -9999:
                    tf = timezonefinder.TimezoneFinder()
                    tz = tf.timezone_at(lng=lon, lat=lat)
                    ds.globalattributes["time_zone"] = tz
                else:
                    logger.warning("Global attributes: unable to define time zone")
                    ds.globalattributes["time_zone"] = ""
    # add or change global attributes as required
    gattr_list = sorted(list(cfg["Global"].keys()))
    for gattr in gattr_list:
        ds.globalattributes[gattr] = cfg["Global"][gattr]
    # remove deprecated global attributes
    flag_list = [g for g in ds.globalattributes.keys() if "Flag" in g]
    others_list = ["end_datetime", "start_datetime", "doi"]
    remove_list = others_list + flag_list
    for gattr in list(ds.globalattributes.keys()):
        if gattr in remove_list:
            ds.globalattributes.pop(gattr)
    # rename global attributes
    rename_dict = {"EPDversion":"PythonVersion", "elevation":"altitude"}
    for item in rename_dict:
        if item in list(ds.globalattributes.keys()):
            new_key = rename_dict[item]
            ds.globalattributes[new_key] = ds.globalattributes.pop(item)
    return

def nc_update(cfg):
    """
    Purpose:
     Update a PFP-style netCDF file by changing variable names and attributes.
    Usage:
    Author: PRI
    Date: October 2018
    """
    nc_file_path = pfp_io.get_infilenamefromcf(cfg)
    ds = pfp_io.nc_read_series(nc_file_path)
    change_variable_names(cfg, ds)
    copy_ws_wd(ds)
    remove_variables(cfg, ds)
    change_global_attributes(cfg, ds)
    nc_file = pfp_io.nc_open_write(nc_file_path)
    pfp_io.nc_write_series(nc_file, ds)
    return 0
