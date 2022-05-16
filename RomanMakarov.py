"""
    Introduction to Artificial Intelligence

    Assignment 2: Accompaniment Generation

    Roman Makarov BS20-06
    o.makarov@innopolis.university
"""
import mido
import music21
import pretty_midi

import random
import shutil


# The name of the input file
_file_name = 'input1.mid'
# _file_name = 'input2.mid'
# _file_name = 'input3.mid'
#


def get_tempo_and_beats_per_bar(mid):
    """
    A function that gets song tempo based on the midi file and number of beats per bar based on the midi file
    :param mid: MidiFile of the song
    :return: Tempo value of the provided input song and number of beats per bar
    """
    __tempo = 50000
    __time_signature = 4

    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                __tempo = msg.tempo
            elif msg.type == 'time_signature':
                __time_signature = msg.numerator

    return __tempo, __time_signature


def get_bars(analysing_file=_file_name):
    """
    A function that gets following information about the song in the midi file:
        * Complete sequence of bars
        * Tempo of the song
        * Number of bars per beat
        * Durance of each bar
    :param analysing_file: Path to the input file
    :return: List of bars, tempo, number of bars in per beat, durance of each bar
    """
    song_data = pretty_midi.PrettyMIDI(analysing_file)
    mid = mido.MidiFile(analysing_file, clip=True)

    _bars = list()
    _bar = 1
    _current_bar = list()

    _tempo, _bar_num = get_tempo_and_beats_per_bar(mid)
    _bar_durance = _bar_num * _tempo / (2 * pow(10, 6))

    for instrument in song_data.instruments:
        for note in instrument.notes:
            if note.start >= _bar_durance * _bar:
                _bar += 1
                _bars.append(_current_bar)
                _current_bar = list()

            _current_bar.append((note.pitch, round(note.start, 2), round(note.end, 2)))

    return _bars, _tempo, _bar_num, _bar_durance


# Global variables that are needed in the code
global file_name, key_tonic, mode, bars, tempo, bar_num, bar_durance, total_bars, scale
global number_of_chords


def input_analysis(_file_name):
    """
    A function that finalizes the following information about the input song:
        * Name of the file
        * Tonic and mode of the song
        * Complete list of bars in the song
        * Tempo of the sing
        * Number of bars per beat and their duration
        * Total number of bars
        * Scale for the notes that can be used in the complement
    :param _file_name: Path to the input file
    :return: Created global variables
    """
    global file_name, key_tonic, mode, bars, tempo, bar_num, bar_durance, total_bars, scale
    global number_of_chords

    file_name = _file_name

    music_info = music21.converter.parse(file_name)
    key = music_info.analyze('key')

    number_of_chords = 3
    key_tonic = key.tonic.name
    mode = key.mode

    bars, tempo, bar_num, bar_durance = get_bars(file_name)

    total_bars = len(bars) // 2

    key_mode = key_tonic + ' ' + mode
    if key_mode == 'G minor':
        key_mode = 'C major'
    elif key_mode == 'H minor':
        key_mode = 'D major'
    elif key_mode == 'A minor':
        key_mode = 'B major'
    elif key_mode == 'C#':
        key_mode = 'E major'
    elif key_mode == 'E minor':
        key_mode = 'G major'
    elif key_mode == 'D minor':
        key_mode = 'F major'

    # Ranges of notes that can be used for a scale
    scales = {'B major': [43, 45, 46, 48, 50, 51, 53, 55, 57],
              'C major': [45, 47, 48, 50, 52, 53, 55, 57, 59],
              'D major': [49, 50, 52, 54, 55, 57, 59, 61, 62],
              'E major': [49, 51, 52, 54, 56, 47, 59, 61, 63],
              'F major': [48, 50, 52, 53, 55, 57, 58, 60, 62],
              'G major': [48, 50, 52, 54, 55, 57, 59, 60, 62]
              }

    try:
        scale = scales[key_mode]
    except:
        scale = scales['F major']


class Individual:
    """
    A class which represents one individual in the Evolutionary algorithm.
    It has the following properties:
        * One individual consists of the whole list of chords for the song
        * Initially it is generated either randomly or through crossover
        * Each individual has a fitness function that evaluates its correspondence to the task
    """
    def __init__(self, _genome=None):
        self.genome = list()
        self.fitness = 0
        self.N = total_bars * 2
        self.scale = scale
        self.number_of_chords = number_of_chords

        if _genome is None:
            self.genome = [self.random_genome(self.number_of_chords) for _ in range(self.N)]
        else:
            self.genome = _genome

    def __str__(self):
        return 'Genome:\n' + str(self.genome)

    def random_genome(self, _number_of_chords):
        """
        A function for that returns required number of chords within the scale
        :param _number_of_chords: required number of chords generated
        :return: k random chords from a song's scale
        """
        return random.choices(self.scale, k=_number_of_chords)

    def fitness_function(self):
        """
        A function that computes fitness value for an individual using:
            1) Check for the notes in the chord to be distinct
            2) Check for the notes not to be close to each other, that is:
                If two notes are too close (next to each other) then they
                do not sound, so we have to avoid these situations
        """
        _fitness_value = 100

        # Constants for computing fitness value
        penalty_for_distinct_notes = 50
        penalty_for_close_notes = 200

        for i in range(len(self.genome)):
            if not isinstance(self.genome[i], list):
                break

            values = sorted(self.genome[i])
            distinct_values = set(values)

            # Check for 3 different notes in the chord
            if len(distinct_values) < 3:
                _fitness_value -= penalty_for_distinct_notes

            # Check for the notes in the chord not to be close to each other
            for ii in range(len(values)):
                for jj in range(ii + 1, min(len(values), ii + 2)):
                    _fitness_value += penalty_for_close_notes if (values[jj] - values[ii] > 2) else 0

        return _fitness_value

    def mutation(self):
        """
        A function that does the random mutation for an individual using following steps:
            1) Check randomly (with probability 10%) if we need to do a mutation on a current chord
            2) If 1st condition holds, proceed with replacing the chord with the random new one
        """
        for i in range(len(self.genome)):
            change_number = random.uniform(0, 1)
            if change_number < 0.1:
                self.genome = self.genome[:i] + self.random_genome(self.number_of_chords) + self.genome[i + 1:]


# The helping function that returns fitness function for an individual
def fitness_value(individual: Individual):
    return individual.fitness


class EvolutionaryAlgorithm:
    """
    A class for simulating an evolutionary algorithm in the next steps:
        0) Create the needed number of individuals
        1) Do the selection procedure and choose 40% of the population based on the fitness function
        2) Do the crossover on the 40% of the population
        3) If there are fewer individuals than required, add new randomly generated ones
        4) Update fitness values for each individual
    """
    def __init__(self, _n, _n_evol_steps):
        self.number_of_individuals = _n
        self.number_of_evolutionary_steps = _n_evol_steps
        self.number_of_survivals = round(_n * 0.4)
        self.population = list()

        self.generate_individuals(self.number_of_individuals)
        self.update_fitness_value()

    def generate_individuals(self, required_number):
        """
        A function that generates provided number of new individuals
        :param required_number: The number of needed individuals in the population
        """
        for i in range(required_number):
            self.population.append(Individual())

    def evolution(self):
        """
        A function that generates the evolution process by the steps that were
        described in the beginning of the class
        :return:
        """
        for i in range(self.number_of_evolutionary_steps):
            self.selection()
            self.cross_over()
            if len(self.population) < self.number_of_individuals:
                self.generate_individuals(self.number_of_individuals - len(self.population))
            self.update_fitness_value()

    def selection(self):
        """
        A function that does the selection process for the individuals
        """
        self.population = sorted(self.population, key=fitness_value, reverse=True)[:self.number_of_survivals]

    def cross_over(self):
        """
        A function that simulates a crossover by going through all survived
        individuals and randomly crossing their genes over to get a new individual
        """
        new_individuals = list()

        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                take_second_genes_from = random.randint(0, len(self.population[0].genome))
                take_second_genes_until = random.randint(0, len(self.population[0].genome))

                if take_second_genes_from > take_second_genes_until:
                    take_second_genes_from, take_second_genes_until = take_second_genes_until, take_second_genes_from

                new_individual_genome = self.population[i].genome[:take_second_genes_from]
                new_individual_genome.extend(self.population[j].genome[take_second_genes_from:take_second_genes_until])
                new_individual_genome.extend(self.population[i].genome[take_second_genes_until:])

                new_individual = Individual(new_individual_genome)
                new_individual.mutation()

                new_individuals.append(new_individual)

        self.population.extend(new_individuals)

    def update_fitness_value(self):
        """
        A function that updates fitness value for all currently alive individuals
        """
        for individual in self.population:
            individual.fitness_function()


def create_mid_file(chords, given_file_name):
    """
    A function that creates new midi file after evolutionary algorithm picked the best
    :param chords: List of chords for the complement
    :param given_file_name: Initial name of the file
    """
    src = f'./{given_file_name}'
    dst = f"./result_{given_file_name}"

    shutil.copy(src, dst)

    mid = mido.MidiFile(dst, clip=True)

    track = mido.MidiTrack()

    VELOCITY = 50
    try:
        VELOCITY = mid.tracks[1][2].velocity
        if not isinstance(VELOCITY, int):
            raise ValueError
    except:
        VELOCITY = 50

    CHORD_TICKS = mid.ticks_per_beat * 2

    # Add chords to the file as a new track
    for chord in chords.genome:
        track.append(mido.Message('note_on',  channel=0, note=chord[0], velocity=VELOCITY, time=0))
        track.append(mido.Message('note_on',  channel=0, note=chord[1], velocity=VELOCITY, time=0))
        track.append(mido.Message('note_on',  channel=0, note=chord[2], velocity=VELOCITY, time=0))
        track.append(mido.Message('note_off', channel=0, note=chord[0], velocity=VELOCITY, time=CHORD_TICKS))
        track.append(mido.Message('note_off', channel=0, note=chord[1], velocity=VELOCITY, time=0))
        track.append(mido.Message('note_off', channel=0, note=chord[2], velocity=VELOCITY, time=0))
    mid.tracks.append(track)

    mid.save(f'./result_{given_file_name}')


def main():
    """
    A function that runs all the process:
        1) Song analysis
        2) Evolutionary algorithm
        3) Creation of the new file with complement
    """
    try:
        input_analysis(_file_name)
    except:
        print('Error while input analysis')
        exit(0)

    # Constants for the evolutionary algorithm
    number_of_individuals = 10
    number_of_epochs = 100

    evolutionary_algorithm = EvolutionaryAlgorithm(number_of_individuals, number_of_epochs)
    try:
        evolutionary_algorithm.evolution()
    except:
        print('An exception occurred during evolution process')
        exit(0)

    best_individual = evolutionary_algorithm.population[0]
    try:
        create_mid_file(chords=best_individual, given_file_name=_file_name)
    except:
        print('The error while creating a file')


main()
