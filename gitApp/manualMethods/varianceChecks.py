import matplotlib.pyplot as plt
from mongoDocuments import Config, Setup, Result
import numpy as np

import os
import mongoengine as me


def allPlot(name, data):
	fig, ax = plt.subplots(1, figsize=(16/2, 9/2), dpi=300)
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
	fig.savefig(f'figs/{name}_measurements.png', dpi=300)


def minMeanScatterPlot(name, data, labels):
	data = np.array(data)
	mins = np.min(data, axis=1)
	means = np.mean(data, axis=1)
	ratio = mins/means
	fig = plt.figure(figsize=(10, max(len(data)/10, 5)), dpi=300)
	plt.boxplot(data.T / data.T.min(axis=0), vert=False)
	plt.title(f'{name} boxplot ')
	plt.ylabel('Configuration')
	plt.xlabel('Min normalized time')
	plt.grid(which='both', axis='y', linestyle=':')
	plt.yticks(np.arange(1, len(data)+1), labels, rotation='horizontal', fontsize=8)
	#plt.gcf().subplots_adjust(bottom=.5)
	# plt.ylim(0, 1)
	plt.show()
	fig.savefig(f'figs/{name}_boxplot.png', dpi=300)


if __name__ == '__main__':

	me.connect('performancedb', host=os.environ['MONGOHOST'], username=os.environ['USERNAME'], password=os.environ['PASSWORD'])

	# New setups with more tuning-samples and changed rebuild frequency
	homoID = '5f44050def458403b65f97fa'
	imhomoID = '5f44050def458403b65f97f9'
	sha = '20382287f7f3d1ff2aa8414891ea657245670c80'

	homo = Setup.objects().get(id=homoID)
	inhomo = Setup.objects().get(id=imhomoID)

	for s_name, setup in zip(['homo', 'inhomo'], [homo, inhomo]):
		configs = Config.objects(setup=setup, commitSHA=sha)

		# TODO: Remove limit here
		for conf in configs:
			results = list(Result.objects(config=conf))  # [:10]
			data = []
			labels = []
			for res in results:
				res: Result
				resDict = res.__dict__
				keys = [k for k in resDict.keys() if 'dynamic' in k and '_dynamic_lock' not in k]
				labels.append(''.join([f'{str(resDict[k])} ' for k in keys]))
				data.append(res.measurements)
			data = np.array(data)

			# TODO: Watch out for rebuild freq change
			rebuild_freq = 4
			data_rebuild = [d[::rebuild_freq] for d in data]
			data_nonrebuild = [[d[i] for i in range(len(d)) if i % rebuild_freq != 0] for d in data]

			all_name = f'{s_name}: all measurements'
			allPlot(all_name, data)
			# minMeanScatterPlot('TEST', [[1, 1, 10], [1, 1, 20], [1, 1, 30]], ['0', '1', '2'])
			minMeanScatterPlot(all_name, data, labels)
			rebuild_name = f'{s_name}: only rebuild'
			allPlot(rebuild_name, data_rebuild)
			minMeanScatterPlot(rebuild_name, data_rebuild, labels)
			nonrebuild_name = f'{s_name}: only non-rebuild'
			allPlot(nonrebuild_name, data_nonrebuild)
			minMeanScatterPlot(nonrebuild_name, data_nonrebuild, labels)

			print(len(results))
