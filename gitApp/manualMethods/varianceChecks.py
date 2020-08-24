import matplotlib.pyplot as plt
from mongoDocuments import Config, Setup, Result
import numpy as np

import os
import mongoengine as me


def allPlot(name, data):
	fig, ax = plt.subplots(1, figsize=(16, 9), dpi=300)
	ax.set_title(name)
	maxVal = 0
	for d in data:
		minned = d / np.min(d)
		ax.plot(minned, alpha=.5)
		maxVal = maxVal if maxVal > minned.max() else minned.max()
	ax.set_ylim(0, maxVal)
	ax.set_xlabel('# Measurement')
	ax.set_ylabel('Min normalized time')
	plt.grid(which='both', linestyle=':')
	plt.show()


def minMeanScatterPlot(name, data):
	data = np.array(data)
	mins = np.min(data, axis=1)
	means = np.mean(data, axis=1)
	ratio = mins/means
	fig = plt.figure(figsize=(20, 5), dpi=300)
	plt.boxplot(data.T / data.T.min(axis=0))
	plt.title(f'{name} boxplot ')
	plt.xlabel('Configuration')
	plt.ylabel('Min normalized time')
	plt.grid(which='both', axis='y', linestyle=':')
	# plt.ylim(0, 1)
	plt.show()


if __name__ == '__main__':

	me.connect('performancedb', host=os.environ['MONGOHOST'], username=os.environ['USERNAME'], password=os.environ['PASSWORD'])

	# New setups with more tuning-samples and changed rebuild frequency
	homoID = '5f44050def458403b65f97fa'
	imhomoID = '5f44050def458403b65f97f9'

	homo = Setup.objects().get(id=homoID)
	inhomo = Setup.objects().get(id=imhomoID)

	for s_name, setup in zip(['homo', 'inhomo'], [homo, inhomo]):
		configs = Config.objects(setup=setup)

		# TODO: Remove limit here
		for conf in configs[0:1]:
			results = list(Result.objects(config=conf))
			data = []
			for res in results:
				res: Result
				data.append(res.measurements)
			data = np.array(data)

			# TODO: Watch out for rebuild freq change
			rebuild_freq = 4
			data_rebuild = [d[::rebuild_freq] for d in data]
			data_nonrebuild = [[d[i] for i in range(len(d)) if i % rebuild_freq != 0] for d in data]

			all_name = f'{s_name}: all measurements'
			allPlot(all_name, data)
			minMeanScatterPlot(all_name, data)
			rebuild_name = f'{s_name}: only rebuild'
			allPlot(rebuild_name, data_rebuild)
			minMeanScatterPlot(rebuild_name, data_rebuild)
			nonrebuild_name = f'{s_name}: only non-rebuild'
			allPlot(nonrebuild_name, data_nonrebuild)
			minMeanScatterPlot(nonrebuild_name, data_nonrebuild)

			print(len(results))
