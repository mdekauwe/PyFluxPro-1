# standard modules
import datetime
import logging
# 3rd party
import dateutil
import numpy
# PFP modules
import meteorologicalfunctions as pfp_mf
import pfp_utils

logger = logging.getLogger("pfp_log")

def AhfromRH(ds, Ah_out, RH_in, Ta_in):
    """
    Purpose:
     Function to calculate absolute humidity given relative humidity and
     air temperature.  Absolute humidity is not calculated if any of the
     input series are missing or if the specified output series already
     exists in the data structure.
     The calculated absolute humidity is created as a new series in the
     data structure.
    Usage:
     pfp_func.AhfromRH(ds,"Ah_HMP_2m","RH_HMP_2m","Ta_HMP_2m")
    Author: PRI
    Date: September 2015
    """
    nRecs = int(ds.globalattributes["nc_nrecs"])
    zeros = numpy.zeros(nRecs,dtype=numpy.int32)
    ones = numpy.ones(nRecs,dtype=numpy.int32)
    for item in [RH_in,Ta_in]:
        if item not in ds.series.keys():
            msg = " AhfromRH: Requested series "+item+" not found, "+Ah_out+" not calculated"
            logger.error(msg)
            return 0
    if Ah_out in ds.series.keys():
        msg = " AhfromRH: Output series "+Ah_out+" already exists, skipping ..."
        logger.error(msg)
        return 0
    RH_data,RH_flag,RH_attr = pfp_utils.GetSeriesasMA(ds,RH_in)
    Ta_data,Ta_flag,Ta_attr = pfp_utils.GetSeriesasMA(ds,Ta_in)
    Ah_data = pfp_mf.absolutehumidityfromRH(Ta_data,RH_data)
    Ah_attr = pfp_utils.MakeAttributeDictionary(long_name="Absolute humidity calculated from "+RH_in+" and "+Ta_in,
                                              height=RH_attr["height"],
                                              units="g/m3")
    flag = numpy.where(numpy.ma.getmaskarray(Ah_data)==True,ones,zeros)
    pfp_utils.CreateSeries(ds,Ah_out,Ah_data,flag,Ah_attr)
    return 1

def AhfromMR(ds, Ah_out, MR_in, Ta_in, ps_in):
    """
    Purpose:
     Function to calculate absolute humidity given the water vapour mixing
     ratio, air temperature and pressure.  Absolute humidity is not calculated
     if any of the input series are missing or if the specified output series
     already exists in the data structure.
     The calculated absolute humidity is created as a new series in the
     data structure.
    Usage:
     pfp_func.AhfromMR(ds,"Ah_IRGA_Av","H2O_IRGA_Av","Ta_HMP_2m","ps")
    Author: PRI
    Date: September 2015
    """
    nRecs = int(ds.globalattributes["nc_nrecs"])
    zeros = numpy.zeros(nRecs,dtype=numpy.int32)
    ones = numpy.ones(nRecs,dtype=numpy.int32)
    for item in [MR_in,Ta_in,ps_in]:
        if item not in ds.series.keys():
            msg = " AhfromMR: Requested series "+item+" not found, "+Ah_out+" not calculated"
            logger.error(msg)
            return 0
    if Ah_out in ds.series.keys():
        msg = " AhfromMR: Output series "+Ah_out+" already exists, skipping ..."
        logger.error(msg)
        return 0
    MR_data,MR_flag,MR_attr = pfp_utils.GetSeriesasMA(ds,MR_in)
    Ta_data,Ta_flag,Ta_attr = pfp_utils.GetSeriesasMA(ds,Ta_in)
    ps_data,ps_flag,ps_attr = pfp_utils.GetSeriesasMA(ds,ps_in)
    Ah_data = pfp_mf.h2o_gpm3frommmolpmol(MR_data,Ta_data,ps_data)
    long_name = "Absolute humidity calculated from "+MR_in+", "+Ta_in+" and "+ps_in
    Ah_attr = pfp_utils.MakeAttributeDictionary(long_name=long_name,
                                              height=MR_attr["height"],
                                              units="g/m3")
    flag = numpy.where(numpy.ma.getmaskarray(Ah_data)==True,ones,zeros)
    pfp_utils.CreateSeries(ds,Ah_out,Ah_data,flag,Ah_attr)
    return 1

def ConvertK2C(ds, T_out, T_in):
    """
    Purpose:
     Function to convert temperature from K to C.
    Usage:
     pfp_func.ConvertK2C(ds, T_out, T_in)
    Author: PRI
    Date: February 2018
    """
    if T_in not in ds.series.keys():
        msg = " ConvertK2C: variable " + T_in + " not found, skipping ..."
        logger.warning(msg)
        return 0
    if "<" in T_out or ">" in T_out:
        logger.warning(" ***")
        msg = " *** " + T_in + ": illegal name (" + T_out + ") in function, skipping ..."
        logger.warning(msg)
        logger.warning(" ***")
        return 0
    var_in = pfp_utils.GetVariable(ds, T_in)
    var_out = pfp_utils.convert_units_func(ds, var_in, "C", mode="quiet")
    var_out["Label"] = T_out
    pfp_utils.CreateVariable(ds, var_out)
    return 1

def ConvertPa2kPa(ds, ps_out, ps_in):
    """
    Purpose:
     Function to convert pressure from Pa to kPa.
    Usage:
     pfp_func.ConvertPa2kPa(ds, ps_out, ps_in)
    Author: PRI
    Date: February 2018
    """
    var_in = pfp_utils.GetVariable(ds, ps_in)
    var_out = pfp_utils.convert_units_func(ds, var_in, "kPa", mode="quiet")
    var_out["Label"] = ps_out
    pfp_utils.CreateVariable(ds, var_out)
    return 1

def ConverthPa2kPa(ds, ps_out, ps_in):
    """
    Purpose:
     Function to convert pressure from hPa (mb) to kPa.
    Usage:
     pfp_func.ConverthPa2kPa(ds, ps_in, ps_out)
    Author: PRI
    Date: February 2018
    """
    var_in = pfp_utils.GetVariable(ds, ps_in)
    var_out = pfp_utils.convert_units_func(ds, var_in, "kPa", mode="quiet")
    var_out["Label"] = ps_out
    pfp_utils.CreateVariable(ds, var_out)
    return 1

def ConvertRHtoPercent(ds, RH_out, RH_in):
    """
    Purpose:
     Function to convert RH in units of "frac" (0 to 1) to "percent" (1 to 100).
    Usage:
     pfp_func.ConvertRHtoPercent(ds, RH_out, RH_in)
    Author: PRI
    Date: August 2019
    """
    var_in = pfp_utils.GetVariable(ds, RH_in)
    var_out = pfp_utils.convert_units_func(ds, var_in, "%", mode="quiet")
    var_out["Label"] = RH_out
    pfp_utils.CreateVariable(ds, var_out)
    return

def DateTimeFromDoY(ds, dt_out, Year_in, DoY_in, Hdh_in):
    year,f,a = pfp_utils.GetSeriesasMA(ds,Year_in)
    doy,f,a = pfp_utils.GetSeriesasMA(ds,DoY_in)
    hdh,f,a = pfp_utils.GetSeriesasMA(ds,Hdh_in)
    idx = numpy.ma.where((numpy.ma.getmaskarray(year)==False)&
                         (numpy.ma.getmaskarray(doy)==False)&
                         (numpy.ma.getmaskarray(hdh)==False))[0]
    year = year[idx]
    doy = doy[idx]
    hdh = hdh[idx]
    hour = numpy.array(hdh,dtype=numpy.integer)
    minute = numpy.array((hdh-hour)*60,dtype=numpy.integer)
    dt = [datetime.datetime(int(y),1,1,h,m)+datetime.timedelta(int(d)-1) for y,d,h,m in zip(year,doy,hour,minute)]
    nRecs = len(dt)
    ds.series[dt_out] = {}
    ds.series[dt_out]["Data"] = dt
    ds.series[dt_out]["Flag"] = numpy.zeros(len(dt),dtype=numpy.int32)
    ds.series[dt_out]["Attr"] = {}
    ds.series[dt_out]["Attr"]["long_name"] = "Datetime in local timezone"
    ds.series[dt_out]["Attr"]["units"] = "None"
    # now remove any "data"" from empty lines
    series_list = ds.series.keys()
    if dt_out in series_list: series_list.remove(dt_out)
    for item in series_list:
        ds.series[item]["Data"] = ds.series[item]["Data"][idx]
        ds.series[item]["Flag"] = ds.series[item]["Flag"][idx]
    ds.globalattributes["nc_nrecs"] = nRecs
    return 1

def DateTimeFromTimeStamp(ds, dt_out, TimeStamp_in, fmt=""):
    if TimeStamp_in not in ds.series.keys():
        logger.error(" Required series "+TimeStamp_in+" not found")
        return 0
    TimeStamp = ds.series[TimeStamp_in]["Data"]
    # guard against empty fields in what we assume is the datetime
    idx = [i for i in range(len(TimeStamp)) if len(str(TimeStamp[i]))>0]
    if len(fmt)==0:
        dt = [dateutil.parser.parse(str(TimeStamp[i])) for i in idx]
    else:
        yearfirst = False
        dayfirst = False
        if fmt.index("Y") < fmt.index("D"): yearfirst = True
        if fmt.index("D") < fmt.index("M"): dayfirst = True
        dt = [dateutil.parser.parse(str(TimeStamp[i]),dayfirst=dayfirst,yearfirst=yearfirst)
              for i in idx]
    # we have finished with the timestamp so delete it from the data structure
    del ds.series[TimeStamp_in]
    nRecs = len(dt)
    ds.series[dt_out] = {}
    ds.series[dt_out]["Data"] = dt
    ds.series[dt_out]["Flag"] = numpy.zeros(len(dt),dtype=numpy.int32)
    ds.series[dt_out]["Attr"] = {}
    ds.series[dt_out]["Attr"]["long_name"] = "Datetime in local timezone"
    ds.series[dt_out]["Attr"]["units"] = "None"
    # now remove any "data"" from empty lines
    series_list = ds.series.keys()
    if dt_out in series_list: series_list.remove(dt_out)
    for item in series_list:
        ds.series[item]["Data"] = ds.series[item]["Data"][idx]
        ds.series[item]["Flag"] = ds.series[item]["Flag"][idx]
    ds.globalattributes["nc_nrecs"] = nRecs
    return 1

def DateTimeFromExcelDateAndTime(ds, dt_out, xlDate, xlTime):
    """ Get Datetime from Excel date and time fields."""
    xldate = ds.series[xlDate]
    xltime = ds.series[xlTime]
    nrecs = len(xldate["Data"])
    xldatetime = pfp_utils.CreateEmptyVariable("xlDateTime", nrecs)
    xldatetime["Data"] = xldate["Data"] + xltime["Data"]
    xldatetime["Attr"]["long_name"] = "Date/time in Excel format"
    xldatetime["Attr"]["units"] = "days since 1899-12-31 00:00:00"
    pfp_utils.CreateVariable(ds, xldatetime)
    pfp_utils.get_datetime_from_xldate(ds)
    return 1

def DateTimeFromDateAndTimeString(ds, dt_out, Date, Time):
    if Date not in ds.series.keys():
        logger.error(" Requested date series "+Date+" not found")
        return 0
    if Time not in ds.series.keys():
        logger.error(" Requested time series "+Time+" not found")
        return 0
    DateString = ds.series[Date]["Data"]
    TimeString = ds.series[Time]["Data"]
    # guard against empty fields in what we assume is the datetime
    idx = [i for i in range(len(DateString)) if len(str(DateString[i]))>0]
    dt = [dateutil.parser.parse(str(DateString[i])+" "+str(TimeString[i])) for i in idx]
    # we have finished with the date and time strings so delete them from the data structure
    del ds.series[Date], ds.series[Time]
    nRecs = len(dt)
    ds.series[dt_out] = {}
    ds.series[dt_out]["Data"] = dt
    ds.series[dt_out]["Flag"] = numpy.zeros(len(dt),dtype=numpy.int32)
    ds.series[dt_out]["Attr"] = {}
    ds.series[dt_out]["Attr"]["long_name"] = "Datetime in local timezone"
    ds.series[dt_out]["Attr"]["units"] = "None"
    # now remove any "data"" from empty lines
    series_list = ds.series.keys()
    if dt_out in series_list: series_list.remove(dt_out)
    for item in series_list:
        ds.series[item]["Data"] = ds.series[item]["Data"][idx]
        ds.series[item]["Flag"] = ds.series[item]["Flag"][idx]
    ds.globalattributes["nc_nrecs"] = nRecs
    return 1

def MRfromAh(ds, MR_out, Ah_in, Ta_in, ps_in):
    """
    Purpose:
     Calculate H2O mixing ratio from absolute humidity (Ah).
    """
    nRecs = int(ds.globalattributes["nc_nrecs"])
    zeros = numpy.zeros(nRecs,dtype=numpy.int32)
    ones = numpy.ones(nRecs,dtype=numpy.int32)
    for item in [Ah_in, Ta_in, ps_in]:
        if item not in ds.series.keys():
            msg = " MRfromAh: Requested series "+item+" not found, "+MR_out+" not calculated"
            logger.error(msg)
            return 0
    if MR_out in ds.series.keys():
        msg = " MRfromAh: Output series "+MR_out+" already exists, skipping ..."
        logger.error(msg)
        return 0
    Ah_data,Ah_flag,Ah_attr = pfp_utils.GetSeriesasMA(ds, Ah_in)
    Ta_data,Ta_flag,Ta_attr = pfp_utils.GetSeriesasMA(ds, Ta_in)
    ps_data,ps_flag,ps_attr = pfp_utils.GetSeriesasMA(ds, ps_in)
    MR_data = pfp_mf.h2o_mmolpmolfromgpm3(Ah_data, Ta_data, ps_data)
    MR_attr = pfp_utils.MakeAttributeDictionary(long_name="H2O mixing ratio calculated from "+Ah_in+", "+Ta_in+" and "+ps_in,
                                              height=Ah_attr["height"],
                                              units="mmol/mol")
    flag = numpy.where(numpy.ma.getmaskarray(MR_data)==True,ones,zeros)
    pfp_utils.CreateSeries(ds, MR_out, MR_data, flag, MR_attr)
    return 1

def MRfromRH(ds, MR_out, RH_in, Ta_in, ps_in):
    """
    Purpose:
     Calculate H2O mixing ratio from RH.
    """
    nRecs = int(ds.globalattributes["nc_nrecs"])
    zeros = numpy.zeros(nRecs,dtype=numpy.int32)
    ones = numpy.ones(nRecs,dtype=numpy.int32)
    for item in [RH_in, Ta_in, ps_in]:
        if item not in ds.series.keys():
            msg = " MRfromRH: Requested series "+item+" not found, "+MR_out+" not calculated"
            logger.error(msg)
            return 0
    if MR_out in ds.series.keys():
        msg = " MRfromRH: Output series "+MR_out+" already exists, skipping ..."
        logger.error(msg)
        return 0
    RH_data,RH_flag,RH_attr = pfp_utils.GetSeriesasMA(ds, RH_in)
    Ta_data,Ta_flag,Ta_attr = pfp_utils.GetSeriesasMA(ds, Ta_in)
    Ah_data = pfp_mf.absolutehumidityfromRH(Ta_data, RH_data)
    ps_data,ps_flag,ps_attr = pfp_utils.GetSeriesasMA(ds, ps_in)
    MR_data = pfp_mf.h2o_mmolpmolfromgpm3(Ah_data, Ta_data, ps_data)
    MR_attr = pfp_utils.MakeAttributeDictionary(long_name="H2O mixing ratio calculated from "+RH_in+", "+Ta_in+" and "+ps_in,
                                              height=RH_attr["height"],
                                              units="mmol/mol")
    flag = numpy.where(numpy.ma.getmaskarray(MR_data)==True,ones,zeros)
    pfp_utils.CreateSeries(ds, MR_out, MR_data, flag, MR_attr)
    return 1