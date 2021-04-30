from .runner import SimulationRunner
from multiprocessing import Pool
from simple_slurm import Slurm


class ParallelRunner(SimulationRunner):

    """
    A Runner which can perform simulations in parallel on the current machine.
    """

    def run_simulations(self, parameter_list, data_folder, stop_on_errors=False):
        """
        This function runs multiple simulations in parallel.

        Args:
            parameter_list (list): list of parameter combinations to simulate.
            data_folder (str): folder in which to create output folders.
        """
        self.data_folder = data_folder
        self.stop_on_errors = stop_on_errors

        # TODO Launch the simulations with SLURM
        for parameter in parameter_list:
            result, command, temp_dir = super.initialize_result(parameter)
            print(result)
            print(command)
            print(temp_dir)
            # slurm = Slurm(
            #     array=range(3, 12),
            #     cpus_per_task=15,
            #     job_name='name',
            #     dependency=dict(after=65541, afterok=34987),
            #     output=f'{Slurm.JOB_ARRAY_MASTER_ID}_{Slurm.JOB_ARRAY_ID}.out',
            # )
            # slurm.sbatch(command)
