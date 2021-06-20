import requests
import json
import pandas as pd
import os
import datetime


class FormulaOne:
    def __init__(self, 
                 data_directory='data', 
                 races_df='races.csv', 
                 circuits_df='circuits.csv', 
                 results_df='results.csv', 
                 drivers_df='drivers.csv', 
                 constructors_df='constructors.csv'):
        self.directory = data_directory
        self._races_df = races_df
        self._circuits_df = circuits_df
        self._results_df = results_df
        self._drivers_df = drivers_df
        self._constructors_df = constructors_df
        
        if self.directory in os.listdir():
            CSV_FILES = [races_df, circuits_df, results_df, 
                         drivers_df, constructors_df]
            if all([c in os.listdir(self.directory) for c in CSV_FILES]):
                self.races = pd.read_csv(
                    os.path.join(self.directory, races_df), index_col=0
                    )
                self.circuits = pd.read_csv(
                    os.path.join(self.directory, circuits_df), index_col=0
                    )
                self.results = pd.read_csv(
                    os.path.join(self.directory, results_df), index_col=0
                    )
                self.drivers = pd.read_csv(
                    os.path.join(self.directory, drivers_df), index_col=0
                    )
                self.constructors = pd.read_csv(
                    os.path.join(self.directory, constructors_df), index_col=0
                    )
            else:
                self.races = None
                self.circuits = None
                self.results = None
                self.drivers = None
                self.constructors = None
        else:
            os.mkdir(self.directory)
            self.races = None
            self.circuits = None
            self.results = None
            self.drivers = None
            self.constructors = None
            
    def _all_data_loaded(self):
        return (
            (not self.races is None) & 
            (not self.circuits is None) &
            (not self.results is None) &
            (not self.drivers is None) &
            (not self.constructors is None)
        )
        
    def _get_race_id(self, data):
        """
        Creates a RaceID from a season and round.
        Keys for ``data`` should be:
            ['season', 'round', 'url', 'raceName', 
             'Circuit', 'date', 'time', 'Results']
        """

        year = data.get('season', 0)
        rnd = data.get('round', 0)
        rnd = rnd if len(rnd) == 2 else f'0{rnd}'
        return int(f"{year}{rnd}")
    
    def _get_race(self, data):
        """
        Returns a row for the RACES table from a Races dictionary.
        Keys for ``data`` should be:
            ['season', 'round', 'url', 'raceName', 
             'Circuit', 'date', 'time', 'Results']
        """

        # Format datetime string.
        d = data.get('date', '1900-01-01')
        t = data.get('time', '01:01:01Z')
        dt_string = f'{d} {t}'

        # Return row.
        return dict(
            RaceID=self._get_race_id(data),
            Season=int(data.get('season', -1)),
            Round=int(data.get('round', -1)),
            RaceName=data.get('raceName'),
            CircuitID=data.get('Circuit').get('circuitId'),
            DateTime=pd.to_datetime(dt_string),
            URL=data.get('url'),
        )

    def _get_circuit(self, data):
        """
        Returns a row for the CIRCUIT table from a Races dictionary.
        Keys for ``data`` should be:
            ['season', 'round', 'url', 'raceName', 
             'Circuit', 'date', 'time', 'Results']
        """

        circuit = data.get('Circuit')
        return dict(
            CircuitID=circuit.get('circuitId'),
            CircuitName=circuit.get('circuitName'),
            Latitude=circuit.get('Location').get('lat'),
            Longitude=circuit.get('Location').get('long'),
            Locality=circuit.get('Location').get('locality'),
            Country=circuit.get('Location').get('country'),
            URL=circuit.get('url'),
        )
    
    def _get_results_drivers_constructors(self, data):
        """
        Returns all rows for a given RaceID for the RESULTS table 
            and all rows for a given RaceID for the DRIVERS table
            and all rows for a given RaceID for the CONSTRUCTORS table
            from a Races dictionary.
        Keys for ``data`` should be:
            ['season', 'round', 'url', 'raceName', 
             'Circuit', 'date', 'time', 'Results']
        """

        RESULTS = []
        DRIVERS = []
        CONSTRUCTORS = []
        race_id = self._get_race_id(data)

        results = data.get('Results')
        for r in results:
            driver = r.get('Driver')
            constructor = r.get('Constructor')

            results_row = dict(
                RaceID=race_id,
                Position=int(r.get('position', -1)),
                Points=int(r.get('points', -1)),
                DriverID=driver.get('driverId'),
                ConstructorID=constructor.get('constructorId'),
                Grid=int(r.get('grid', -1)),
                Laps=int(r.get('laps', -1)),
                Status=r.get('status'),
                Time=r.get('Time').get('time') if r.get('Time') else r.get('Time'),
                FastestLapTime=r.get('FastestLap').get('Time').get('time') \
                    if r.get('FastestLap') else None,
                FastestLapSpeed=r.get('FastestLap').get('AverageSpeed').get('speed') \
                    if r.get('FastestLap') else None
            )
            drivers_row = dict(
                DriverID=driver.get('driverId'),
                Code=driver.get('code'),
                FirstName=driver.get('givenName'),
                LastName=driver.get('familyName'),
                DOB=driver.get('dateOfBirth'),
                Nationality=driver.get('nationality'),
                URL=driver.get('url'),
            )
            constructors_row = dict(
                ConstructorID=constructor.get('constructorId'),
                Name=constructor.get('name'),
                Nationality=constructor.get('nationality'),
                URL=constructor.get('url'),
            )
            RESULTS.append(results_row)
            DRIVERS.append(drivers_row)
            CONSTRUCTORS.append(constructors_row)

        return RESULTS, DRIVERS, CONSTRUCTORS
    
    def _collect_data_from(self, year, round_num=1, verbose=True):
        """
        Collect all data from each event in a given year.

        Returns rows for tables:
            [RACES, CIRCUITS, RESULTS, DRIVERS, CONSTRUCTORS]
        """

        RACES = []
        CIRCUITS = []
        RESULTS = []
        DRIVERS = []
        CONSTRUCTORS = []

        while True:
            URL = f'http://ergast.com/api/f1/{year}/{round_num}/results.json'
            ROUND = requests.get(URL)
            if not ROUND.ok:
                if verbose:
                    print(f'\tComplete. Data from {len(RACES)} races compiled.')
                return RACES, CIRCUITS, RESULTS, DRIVERS, CONSTRUCTORS
            ROUND_DATA = json.loads(ROUND.content)
            data = ROUND_DATA['MRData']['RaceTable']['Races']

            if not data:
                if verbose:
                    print(f'\tComplete. Data from {len(RACES)} races compiled.')
                return RACES, CIRCUITS, RESULTS, DRIVERS, CONSTRUCTORS

            data = data[0]
            if verbose:
                print(f'Collecting data from: Year: {year} | Round: {round_num}')

            RACES.append(self._get_race(data))
            CIRCUITS.append(self._get_circuit(data))
            results, drivers, constructors = \
                self._get_results_drivers_constructors(data)
            RESULTS += results
            DRIVERS += drivers
            CONSTRUCTORS += constructors

            round_num += 1
            
    def _scrape_date_range(self, 
                           start_year, 
                           end_year=None,  
                           verbose=1):
        """
        Scrape data from a given ``start_year`` to a given ``end_year``.

        A directory path can be given as ``save_to`` in order to save the tables 
            in .csv format.
        """
        
        save_to_dir = self.directory
        
        if not end_year:
            end_year = datetime.datetime.now().year
        MICRO_VERBOSE = True if verbose == 2 else False

        ALL_RACES = []
        ALL_CIRCUITS = []
        ALL_RESULTS = []
        ALL_DRIVERS = []
        ALL_CONSTRUCTORS = []

        for year in range(start_year, end_year+1):
            if verbose:
                print(f'Scraping year {year}')
            races, circ, res, dr, const = self._collect_data_from(
                year, verbose=MICRO_VERBOSE)
            ALL_RACES += races
            ALL_CIRCUITS += circ
            ALL_RESULTS += res
            ALL_DRIVERS += dr
            ALL_CONSTRUCTORS += const

        races_df = pd.DataFrame(ALL_RACES)
        circuits_df = pd.DataFrame(ALL_CIRCUITS).drop_duplicates()
        results_df = pd.DataFrame(ALL_RESULTS)
        drivers_df = pd.DataFrame(ALL_DRIVERS).drop_duplicates()
        constructors_df = pd.DataFrame(ALL_CONSTRUCTORS).drop_duplicates()

        if save_to_dir:
            if save_to_dir not in os.listdir():
                os.mkdir(save_to_dir)

            races_df.to_csv(os.path.join(
                save_to_dir, self._races_df))
            circuits_df.to_csv(os.path.join(
                save_to_dir, self._circuits_df))
            results_df.to_csv(os.path.join(
                save_to_dir, self._results_df))
            drivers_df.to_csv(os.path.join(
                save_to_dir, self._drivers_df))
            constructors_df.to_csv(os.path.join(
                save_to_dir, self._constructors_df))

        return races_df, circuits_df, results_df, drivers_df, constructors_df

    def save_data(self):
        """Saves current internal data to ``self.directory``."""
        
        if not self._all_data_loaded():
            return
        
        # Races
        self.races = (
            self.races
            .sort_values('RaceID')
            .reset_index(drop=True)
            .drop_duplicates()
        )
        self.races.to_csv(os.path.join(
            self.directory, self._races_df))
        
        # Circuits
        self.circuits = (
            self.circuits
            .sort_values('CircuitID')
            .reset_index(drop=True)
            .drop_duplicates()
        )
        self.circuits.to_csv(os.path.join(
            self.directory, self._circuits_df))
        
        # Results
        self.results = (
            self.results
            .sort_values(['RaceID', 'Position'])
            .reset_index(drop=True)
            .drop_duplicates()
        )
        self.results.to_csv(os.path.join(
            self.directory, self._results_df))
        
        # Drivers
        self.drivers = (
            self.drivers
            .sort_values('DriverID')
            .reset_index(drop=True)
            .drop_duplicates()
        )
        self.drivers.to_csv(os.path.join(
            self.directory, self._drivers_df))
        
        # Constructors
        self.constructors = (
            self.constructors
            .sort_values('ConstructorID')
            .reset_index(drop=True)
            .drop_duplicates()
        )
        self.constructors.to_csv(os.path.join(
            self.directory, self._constructors_df))
        return f'`.csv` files saved to `{self.directory}`'
            
    def update(
        self, 
        last_results_url='http://ergast.com/api/f1/current/last/results.json'
            ):
        """Update and save data to the most recent season."""
        
        if not self._all_data_loaded():
            return 'No data loaded. Use `.scrape()` instead.'
        
        r = requests.get(last_results_url)
        if not r.ok:
            return f'Request could not be completed. | {r}'
        
        data = json.loads(r.content)['MRData']['RaceTable']['Races'][0]
        race_id = self._get_race_id(data)
        if race_id in set(self.races['RaceID']):
            return f'Data is up to date. | Most Recent RaceID: `{race_id}`'
        
        self.scrape(self.races['Season'].max())
        
    def scrape(self, start_year, end_year=None):
        """
        Scrape from start_year to end_year. Combine currently loaded data 
            and save to ``self.directory``.
        """
        
        (new_races, new_circuits, 
         new_results, new_drivers, 
         new_constructors) = self._scrape_date_range(start_year, end_year)
        
        if self._all_data_loaded():
            self.races = pd.concat(
                [self.races, new_races]).drop_duplicates()
            self.circuits = pd.concat(
                [self.circuits, new_circuits]).drop_duplicates()
            self.results = pd.concat(
                [self.results, new_results]).drop_duplicates()
            self.drivers = pd.concat(
                [self.drivers, new_drivers]).drop_duplicates()
            self.constructors = pd.concat(
                [self.constructors, new_constructors]).drop_duplicates()
        else:
            self.races = new_races
            self.circuits = new_circuits
            self.results = new_results
            self.drivers = new_drivers
            self.constructors = new_constructors
            
        self.save_data()
        return 'Complete!'
            
    def __repr__(self):
        return f'''Data
    Races
        {self.races.shape if not self.races is None else (0, 0)}
    Circuits
        {self.circuits.shape if not self.circuits is None else (0, 0)}
    Results
        {self.results.shape if not self.results is None else (0, 0)}
    Drivers
        {self.drivers.shape if not self.drivers is None else (0, 0)}
    Constructors
        {self.constructors.shape if not self.constructors is None else (0, 0)}
'''