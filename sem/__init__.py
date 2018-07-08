from .manager import CampaignManager
from .runner import SimulationRunner
from .parallelrunner import ParallelRunner
from .database import DatabaseManager
from .utils import list_param_combinations
import click

__all__ = ('CampaignManager', 'SimulationRunner', 'ParallelRunner',
           'DatabaseManager', 'list_param_combinations')

name = 'sem'


@click.command()
def main():
    print("ns-3 Simulation Execution Manager")
