import multiprocessing as mp
import time
from fractions import Fraction

#mat_ref = 0 for mat
#        = 1 for inv
# side = order of the square matrix

class Processor(mp.Process):
	def __init__(self, task_q, result_q):
		mp.Process.__init__(self)
		self.task_q = task_q
		self.result_q = result_q

	def run(self):
		proc_name = self.name
		while True:
			next_task = self.task_q.get() 
			if next_task is None:
				print('Exiting: ', proc_name)
				self.task_q.task_done()
				break
			print(proc_name, ':', next_task)
			res = next_task()
			self.task_q.task_done()
			self.result_q.put(res)
		return


class Result(object):
	def __init__(self, i, j, op, params, prev, mat_ref):
		self.i = i
		self.j = j
		self.op = op
		self.params = params
		self.prev = prev
		self.mat_ref = mat_ref

	def __str__(self):
		return '(%s, %s, %s, %s, %s, %s)' % (self.i, self.j, self.op, self.params, self.prev, self.mat_ref)

class Task(object):
	def __init__(self, i, j, val):
		self.i = i
		self.j = j
		self.val = val

	def __call__(self):
		return Result(self.i, self.j, Fraction(0), 1, self.val, 0)

	def __str__(self):
		return '0 %s %s %s' % (self.i, self.j, self.val)

class Task1(object):
	def __init__(self, i, j, val, scale, mat_ref):
		self.i = i
		self.j = j
		self.val = val
		self.scale = scale
		self.mat_ref = mat_ref

	def __call__(self):
		return Result(self.i, self.j, 1, self.val/self.scale, self.val, self.mat_ref)

	def __str__(self):
		return '1 %s %s %s %s %s' % (self.i, self.j, self.val, self.scale, self.mat_ref)

class Task2(object):
	def __init__(self, i, j, val, sub_val, mat_ref):
		self.i = i
		self.j = j
		self.val = val
		self.sub_val = sub_val
		self.mat_ref = mat_ref

	def __call__(self):
		return Result(self.i, self.j, 2, self.val - self.sub_val, self.val, self.mat_ref)

	def __str__(self):
		return '2 %s %s %s %s %s' % (self.i, self.j, self.val, self.sub_val, self.mat_ref)

def print_mat(mat, n):
	for row in mat:
		for item in row:
			print(item, end=' ')
		print('')

def create_inv(n):
	inv = [[1 if i==j else 0 for j in range(n)] for i in range(n)]
	return inv

def get_mat(file_name):
	with open(file_name, 'r') as f:
		lines = f.readlines()
	side = int(lines[0].strip())
	mat = [[int(x) for x in line.strip().split()] for line in lines[1:]]
	return side, mat

if __name__ == '__main__':

	tasks = mp.JoinableQueue()
	results = mp.Queue()

	side, mat = get_mat('test.txt')
	inv = create_inv(side)

	mat = [[Fraction(val) for val in row] for row in mat]
	inv = [[Fraction(val) for val in row] for row in inv]

	num_proc = side * side
	processors = [Processor(tasks, results) for i in range(num_proc)]

	print('Original Matrix:\n')
	print_mat(mat, side)

	for p in processors:
		p.start()

	for k in range(side):
		print('k =', k)

		tasks.put(Task(k, k, mat[k][k]))
		tasks.join()

		res = results.get()
		if res.op == 0:
			mat[res.i][res.j] = 1

		scale = res.prev
		
		for j in range(k+1, side):
			tasks.put(Task1(k, j, mat[k][j], scale, 0))

		for j in range(side):
			tasks.put(Task1(k, j, inv[k][j], scale, 1))

		tasks.join()

		while results.qsize() > 0:
			res = results.get()
			if res.mat_ref == 0:
				mat[res.i][res.j] = res.params
			elif res.mat_ref == 1:
				inv[res.i][res.j] = res.params

		for i in range(k+1, side):
			factor = mat[i][k]
			for j in range(side):
				tasks.put(Task2(i, j, mat[i][j], factor * mat[k][j], 0))
				tasks.put(Task2(i, j, inv[i][j], factor * inv[k][j], 1))

		tasks.join()

		while results.qsize() > 0:
			res = results.get()
			if res.mat_ref == 0:
				mat[res.i][res.j] = res.params
			elif res.mat_ref == 1:
				inv[res.i][res.j] = res.params

		print_mat(mat, side)
		print_mat(inv, side)

	print('Starting Back trace')

	for k in range(side-1, -1, -1):
		for i in range(k):
			factor = mat[i][k]
			print(factor)
			for j in range(side):
				tasks.put(Task2(i, j, mat[i][j], factor * mat[k][j], 0))
				tasks.put(Task2(i, j, inv[i][j], factor * inv[k][j], 1))

		tasks.join()

		while results.qsize() > 0:
			res = results.get()
			if res.mat_ref == 0:
				mat[res.i][res.j] = res.params
			elif res.mat_ref == 1:
				inv[res.i][res.j] = res.params


	print_mat(mat, side)
	print_mat(inv, side)

	for i in range(num_proc):
		tasks.put(None)

	print("Inverted Matrix:\n")
	print_mat(inv)




