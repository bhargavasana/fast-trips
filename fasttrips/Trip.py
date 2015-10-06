__copyright__ = "Copyright 2015 Contributing Entities"
__license__   = """
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import collections,datetime,os,sys
import numpy,pandas

from .Logger import FastTripsLogger

class Trip:
    """
    Trip class.

    One instance represents all of the transit vehicle trips.

    Stores Trip information in :py:attr:`Trip.trips_df`, an instance of :py:class:`pandas.DataFrame`
    and stop time information in :py:attr:`Trip.stop_times_df`, another instance of
    :py:class:`pandas.DataFrame`.

    Also stores Vehicle information in :py:attr:`Trips.vehicles_df` and
    Service Calendar information in :py:attr:`Trips.service_df`
    """

    #: File with fasttrips trip information (this extends the
    #: `gtfs trips <https://github.com/osplanning-data-standards/GTFS-PLUS/blob/master/files/trips.md>`_ file).
    # See `trips_ft specification <https://github.com/osplanning-data-standards/GTFS-PLUS/blob/master/files/trips_ft.md>`_.
    INPUT_TRIPS_FILE                        = "trips_ft.txt"
    #: gtfs Trips column name: Unique identifier.  This will be the index of the trips table. (object)
    TRIPS_COLUMN_ID                         = 'trip_id'
    #: gtfs Trips column name: Route unique identifier.
    TRIPS_COLUMN_ROUTE_ID                   = 'route_id'
    #: gtfs Trips column name: Service unique identifier.
    TRIPS_COLUMN_SERVICE_ID                 = 'service_id'

    #: fasttrips Trips column name: Vehicle Name
    TRIPS_COLUMN_VEHICLE_NAME               = 'vehicle_name'

    #: File with fasttrips vehicles information.
    #: See `vehicles_ft specification <https://github.com/osplanning-data-standards/GTFS-PLUS/blob/master/files/vehicles_ft.md>`_.
    INPUT_VEHICLES_FILE                     = 'vehicles_ft.txt'
    #: fasttrips Vehicles column name: Vehicle name (identifier)
    VEHICLES_COLUMN_VEHICLE_NAME            = 'vehicle_name'
    #: fasttrips Vehicles column name: Vehicle Description
    VEHICLES_COLUMN_VEHICLE_DESCRIPTION     = 'vehicle_description'
    #: fasttrips Vehicles column name: Seated Capacity
    VEHICLES_COLUMN_SEATED_CAPACITY         = 'seated_capacity'
    #: fasttrips Vehicles column name: Standing Capacity
    VEHICLES_COLUMN_STANDING_CAPACITY       = 'standing_capacity'
    #: fasttrips Vehicles column name: Number of Doors
    VEHICLES_COLUMN_NUMBER_OF_DOORS         = 'number_of_doors'
    #: fasttrips Vehicles column name: Maximum Speed (mph)
    VEHICLES_COLUMN_MAXIMUM_SPEED           = 'max_speed'
    #: fasttrips Vehicles column name: Vehicle Length (feet)
    VEHICLES_COLUMN_VEHICLE_LENGTH          = 'vehicle_length'
    #: fasttrips Vehicles column name: Platform Height (inches)
    VEHICLES_COLUMN_PLATFORM_HEIGHT         = 'platform_height'
    #: fasttrips Vehicles column name: Propulsion Type
    VEHICLES_COLUMN_PROPULSION_TYPE         = 'propulsion_type'
    #: fasttrips Vehicles column name: Wheelchair Capacity (overrides trip)
    VEHICLES_COLUMN_WHEELCHAIR_CAPACITY     = 'wheelchair_capacity'
    #: fasttrips Vehicles column name: Bicycle Capacity
    VEHICLES_COLUMN_BICYCLE_CAPACITY        = 'bicycle_capacity'

    #: fasttrips Service column name: Start Date string in 'YYYYMMDD' format
    SERVICE_COLUMN_START_DATE_STR           = 'start_date_str'
    #: fasttrips Service column name: Start Date as datetime.date
    SERVICE_COLUMN_START_DATE               = 'start_date'
    #: fasttrips Service column name: End Date string in 'YYYYMMDD' format
    SERVICE_COLUMN_END_DATE_STR             = 'end_date_str'
    #: fasttrips Service column name: End Date as datetime.date
    SERVICE_COLUMN_END_DATE                 = 'end_date'

    #: File with fasttrips stop time information (this extends the
    #: `gtfs stop times <https://github.com/osplanning-data-standards/GTFS-PLUS/blob/master/files/stop_times.md>`_ file).
    # See `stop_times_ft specification <https://github.com/osplanning-data-standards/GTFS-PLUS/blob/master/files/stop_times_ft.md>`_.
    INPUT_STOPTIMES_FILE                    = "stop_times_ft.txt"

    #: gtfs Stop times column name: Trip unique identifier. (object)
    STOPTIMES_COLUMN_TRIP_ID                = 'trip_id'
    #: gtfs Stop times column name: Stop unique identifier
    STOPTIMES_COLUMN_STOP_ID                = 'stop_id'
    #: gtfs Stop times column name: Sequence number of stop within a trip.
    #: Starts at 1 and is sequential
    STOPTIMES_COLUMN_STOP_SEQUENCE          = 'stop_sequence'

    #: gtfs Stop times column name: Arrival time string.  e.g. '07:23:05' or '14:08:30'.
    STOPTIMES_COLUMN_ARRIVAL_TIME_STR       = 'arrival_time_str'
    #: Stop times column name: Arrival time.  This is a float, minutes after midnight.
    STOPTIMES_COLUMN_ARRIVAL_TIME_MIN       = 'arrival_time_min'
    #: gtfs Stop times column name: Arrival time.  This is a DateTime.
    STOPTIMES_COLUMN_ARRIVAL_TIME           = 'arrival_time'
    #: Stop times column name: Departure time string. e.g. '07:23:05' or '14:08:30'.
    STOPTIMES_COLUMN_DEPARTURE_TIME_STR     = 'departure_time_str'
    #: Stop times column name: Departure time. This is a float, minutes after midnight.
    STOPTIMES_COLUMN_DEPARTURE_TIME_MIN     = 'departure_time_min'
    #: gtfs Stop times column name: Departure time. This is a DateTime.
    STOPTIMES_COLUMN_DEPARTURE_TIME         = 'departure_time'

    #: gtfs Stop times stop times column name: Stop Headsign
    STOPTIMES_COLUMN_HEADSIGN               = 'stop_headsign'
    #: gtfs Stop times stop times column name: Pickup Type
    STOPTIMES_COLUMN_PICKUP_TYPE            = 'pickup_type'
    #: gtfs Stop times stop times column name: Drop Off Type
    STOPTIMES_COLUMN_DROP_OFF_TYPE          = 'drop_off_type'
    #: gtfs Stop times stop times column name: Shape Distance Traveled
    STOPTIMES_COLUMN_SHAPE_DIST_TRAVELED    = 'shape_dist_traveled'
    #: gtfs Stop times stop times column name: Time Point
    STOPTIMES_COLUMN_TIMEPOINT              = 'timepoint'

    #: Default headway if no previous matching route/trip
    DEFAULT_HEADWAY             = 60

    def __init__(self, input_dir, gtfs_schedule, today):
        """
        Constructor. Read the gtfs data from the transitfeed schedule, and the additional
        fast-trips stops data from the input files in *input_dir*.
        """
        # Combine all gtfs Trip objects to a single pandas DataFrame
        trip_dicts      = []
        stop_time_dicts = []
        for gtfs_trip in gtfs_schedule.GetTripList():
            trip_dict = {}
            for fieldname in gtfs_trip._FIELD_NAMES:
                if fieldname in gtfs_trip.__dict__:
                    trip_dict[fieldname] = gtfs_trip.__dict__[fieldname]
            trip_dicts.append(trip_dict)

            # stop times
            #   _REQUIRED_FIELD_NAMES = ['trip_id', 'arrival_time', 'departure_time',
            #                            'stop_id', 'stop_sequence']
            #   _OPTIONAL_FIELD_NAMES = ['stop_headsign', 'pickup_type',
            #                            'drop_off_type', 'shape_dist_traveled', 'timepoint']
            for gtfs_stop_time in gtfs_trip.GetStopTimes():
                stop_time_dict = {}
                stop_time_dict[Trip.STOPTIMES_COLUMN_TRIP_ID]         = gtfs_trip.__dict__[Trip.STOPTIMES_COLUMN_TRIP_ID]
                stop_time_dict[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME]    = gtfs_stop_time.arrival_time
                stop_time_dict[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME]  = gtfs_stop_time.departure_time
                stop_time_dict[Trip.STOPTIMES_COLUMN_STOP_ID]         = gtfs_stop_time.stop_id
                stop_time_dict[Trip.STOPTIMES_COLUMN_STOP_SEQUENCE]   = gtfs_stop_time.stop_sequence
                # optional fields
                try:
                    stop_time_dict[Trip.STOPTIMES_COLUMN_HEADSIGN]            = gtfs_stop_time.stop_headsign
                except:
                    pass
                try:
                    stop_time_dict[Trip.STOPTIMES_COLUMN_PICKUP_TYPE]         = gtfs_stop_time.pickup_type
                except:
                    pass
                try:
                    top_time_dict[Trip.STOPTIMES_COLUMN_DROP_OFF_TYPE]        = gtfs_stop_time.drop_off_type
                except:
                    pass
                try:
                    stop_time_dict[Trip.STOPTIMES_COLUMN_SHAPE_DIST_TRAVELED] = gtfs_stop_time.shape_dist_traveled
                except:
                    pass
                try:
                    stop_time_dict[Trip.STOPTIMES_COLUMN_TIMEPOINT]           = gtfs_stop_time.timepoint
                except:
                    pass
                stop_time_dicts.append(stop_time_dict)

        self.trips_df = pandas.DataFrame(data=trip_dicts)

        # Read the fast-trips supplemental trips data file
        trips_ft_df = pandas.read_csv(os.path.join(input_dir, "..", Trip.INPUT_TRIPS_FILE),
                                      dtype={Trip.TRIPS_COLUMN_ID:object})
        # verify required columns are present
        trips_ft_cols = list(trips_ft_df.columns.values)
        assert(Trip.TRIPS_COLUMN_ID             in trips_ft_cols)
        assert(Trip.TRIPS_COLUMN_VEHICLE_NAME   in trips_ft_cols)

        # Join to the trips dataframe
        self.trips_df = pandas.merge(left=self.trips_df, right=trips_ft_df,
                                      how='left',
                                      on=Trip.TRIPS_COLUMN_ID)

        self.trips_df.set_index(Trip.TRIPS_COLUMN_ID, inplace=True, verify_integrity=True)

        FastTripsLogger.debug("=========== TRIPS ===========\n" + str(self.trips_df.head()))
        FastTripsLogger.debug("\n"+str(self.trips_df.index.dtype)+"\n"+str(self.trips_df.dtypes))
        FastTripsLogger.info("Read %7d trips" % len(self.trips_df))

        self.vehicles_df = pandas.read_csv(os.path.join(input_dir, "..", Trip.INPUT_VEHICLES_FILE))
        # verify the required columns are present
        vehicle_ft_cols = list(self.vehicles_df.columns.values)
        assert(Trip.VEHICLES_COLUMN_VEHICLE_NAME    in vehicle_ft_cols)

        FastTripsLogger.debug("=========== VEHICLES ===========\n" + str(self.vehicles_df.head()))
        FastTripsLogger.debug("\n"+str(self.vehicles_df.index.dtype)+"\n"+str(self.vehicles_df.dtypes))
        FastTripsLogger.info("Read %7d vehicles" % len(self.vehicles_df))

        service_dicts = []
        for gtfs_service in gtfs_schedule.GetServicePeriodList():
            service_dict = {}
            service_tuple = gtfs_service.GetCalendarFieldValuesTuple()
            for fieldnum in range(len(gtfs_service._FIELD_NAMES)):
                # all required
                fieldname = gtfs_service._FIELD_NAMES[fieldnum]
                service_dict[fieldname] = service_tuple[fieldnum]
            service_dicts.append(service_dict)
        self.service_df = pandas.DataFrame(data=service_dicts)

        # Rename SERVICE_COLUMN_START_DATE to SERVICE_COLUMN_START_DATE_STR
        self.service_df[Trip.SERVICE_COLUMN_START_DATE_STR] = self.service_df[Trip.SERVICE_COLUMN_START_DATE]
        self.service_df[Trip.SERVICE_COLUMN_END_DATE_STR  ] = self.service_df[Trip.SERVICE_COLUMN_END_DATE  ]

        # Convert to datetime
        self.service_df[Trip.SERVICE_COLUMN_START_DATE] = \
            self.service_df[Trip.SERVICE_COLUMN_START_DATE_STR].map(lambda x: \
            datetime.datetime.combine(datetime.datetime.strptime(x, '%Y%M%d').date(), datetime.time(minute=0)))
        self.service_df[Trip.SERVICE_COLUMN_END_DATE] = \
            self.service_df[Trip.SERVICE_COLUMN_END_DATE_STR].map(lambda x: \
            datetime.datetime.combine(datetime.datetime.strptime(x, '%Y%M%d').date(), datetime.time(hour=23, minute=59, second=59, microsecond=999999)))

        FastTripsLogger.debug("=========== SERVICE PERIODS ===========\n" + str(self.service_df.head()))
        FastTripsLogger.debug("\n"+str(self.service_df.index.dtype)+"\n"+str(self.service_df.dtypes))
        FastTripsLogger.info("Read %7d service periods" % len(self.service_df))

        self.stop_times_df = pandas.DataFrame(data=stop_time_dicts)

        # Read the fast-trips supplemental stop times data file
        stop_times_ft_df = pandas.read_csv(os.path.join(input_dir, "..", Trip.INPUT_STOPTIMES_FILE),
                                      dtype={Trip.STOPTIMES_COLUMN_TRIP_ID:object,
                                             Trip.STOPTIMES_COLUMN_STOP_ID:object})
        # verify required columns are present
        stop_times_ft_cols = list(stop_times_ft_df.columns.values)
        assert(Trip.STOPTIMES_COLUMN_TRIP_ID    in stop_times_ft_cols)
        assert(Trip.STOPTIMES_COLUMN_STOP_ID    in stop_times_ft_cols)

        # Join to the trips dataframe
        if len(stop_times_ft_cols) > 2:
            self.stop_times_df = pandas.merge(left=stop_times_df, right=stop_times_ft_df,
                                              how='left',
                                              on=[Trip.STOPTIMES_COLUMN_TRIP_ID,
                                                  Trip.STOPTIMES_COLUMN_STOP_ID])

        FastTripsLogger.debug("=========== STOP TIMES ===========\n" + str(self.stop_times_df.head()))
        FastTripsLogger.debug("\n"+str(self.stop_times_df.index.dtype)+"\n"+str(self.stop_times_df.dtypes))

        # string version - we already have
        self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME_STR]   = self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME]
        self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME_STR] = self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME]

        # datetime version
        self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME] = \
            self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME].map(lambda x: \
                datetime.datetime.combine(today, datetime.datetime.strptime(x, '%H:%M:%S').time()))
        self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME] = \
            self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME].map(lambda x: \
                datetime.datetime.combine(today, datetime.datetime.strptime(x, '%H:%M:%S').time()))

        # float version
        self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME_MIN] = \
            self.stop_times_df[Trip.STOPTIMES_COLUMN_ARRIVAL_TIME].map(lambda x: \
                60*x.time().hour + x.time().minute + x.time().second/60.0 )
        self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME_MIN] = \
            self.stop_times_df[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME].map(lambda x: \
                60*x.time().hour + x.time().minute + x.time().second/60.0 )

        self.stop_times_df.set_index([Trip.STOPTIMES_COLUMN_TRIP_ID,
                                     Trip.STOPTIMES_COLUMN_STOP_SEQUENCE], inplace=True, verify_integrity=True)
        FastTripsLogger.debug("Final\n" + str(self.stop_times_df.head()) + "\n" +str(self.stop_times_df.dtypes) )

        # tell the stops to update accordingly
        # stops.add_trips(self.stop_times_df)

    def get_stop_times(self, trip_id):
        """
        Returns :py:class:`pandas.DataFrame` with stop times for the given trip id.
        """
        return self.stop_times_df.loc[trip_id]

    def number_of_stops(self, trip_id):
        """
        Return the number of stops in this trip.
        """
        return(len(self.stop_times_df.loc[trip_id]))

    def get_scheduled_departure(self, trip_id, stop_id):
        """
        Return the scheduled departure time for the given stop as a datetime.datetime

        TODO: problematic if the stop id occurs more than once in the trip.
        """
        for seq, row in self.stop_times_df.loc[trip_id].iterrows():
            if row[Trip.STOPTIMES_COLUMN_STOP_ID] == stop_id:
                return row[Trip.STOPTIMES_COLUMN_DEPARTURE_TIME]
        raise Exception("get_scheduled_departure: stop %s not find for trip %s" % (str(stop_id), str(trip_id)))

    @staticmethod
    def calculate_dwell_times(trips_df):
        """
        Creates dwell_time in the given :py:class:`pandas.DataFrame` instance.
        """
        trips_df['boardsx4']        = trips_df['boards']*4
        trips_df['alightsx2']       = trips_df['alights']*2
        trips_df['dwell_time']      = trips_df[['boardsx4','alightsx2']].max(axis=1) + 4
        # no boards nor alights -> 0
        trips_df.loc[(trips_df.boards==0)&(trips_df.alights==0), 'dwell_time'] = 0
        # tram, streetcar, light rail -> 30 --- this seems arbitrary
        trips_df.loc[trips_df.service_type==0, 'dwell_time']                   = 30

        # drop our intermediate columns
        trips_df.drop(['boardsx4','alightsx2'], axis=1, inplace=True)

        # print "Dwell time > 0:"
        # print trips_df.loc[trips_df.dwell_time>0]

        # these are integers -- make them as such for now
        trips_df[['dwell_time']] = trips_df[['dwell_time']].astype(int)

    @staticmethod
    def calculate_headways(trips_df):
        """
        Calculates headways and sets them into the given
        trips_df :py:class:`pandas.DataFrame`.

        Returns :py:class:`pandas.DataFrame` with `headway` column added.
        """
        stop_group = trips_df[['stop_id','routeId','direction','depart_time','trip_id','stop_seq']].groupby(['stop_id','routeId','direction'])

        stop_group_df = stop_group.apply(lambda x: x.sort('depart_time'))
        # set headway, in minutes
        stop_group_shift_df = stop_group_df.shift()
        stop_group_df['headway'] = (stop_group_df['depart_time'] - stop_group_shift_df['depart_time'])/numpy.timedelta64(1,'m')
        # zero out the first in each group
        stop_group_df.loc[(stop_group_df.stop_id  !=stop_group_shift_df.stop_id  )|
                          (stop_group_df.routeId  !=stop_group_shift_df.routeId  )|
                          (stop_group_df.direction!=stop_group_shift_df.direction), 'headway'] = Trip.DEFAULT_HEADWAY
        # print stop_group_df

        trips_df_len = len(trips_df)
        trips_df = pandas.merge(left=trips_df, right=stop_group_df[['trip_id','stop_id','stop_seq','headway']],
                                on=['trip_id','stop_id','stop_seq'])
        assert(len(trips_df)==trips_df_len)
        return trips_df
