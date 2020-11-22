
.PHONY: all run dist proto clean

all: proto

proto: raft/raft.proto
	protoc -I=raft --python_out=raft raft/raft.proto

dist:
	python3 setup.py sdist bdist_wheel

clean:
	rm -r build
	rm -r raft_consensus.egg-info
	rm -r dist

upload:
	python3 -m twine upload --repository testpypi dist/*

install:
	python3 -m pip install -e .

uninstall:
	python3 -m pip uninstall raft-concensus

run:
	for i in 0 1 2 3 4; do \
		gnome-terminal -- bash -c "./example/example_1.py --server_count 5 --id $$i; bash"; \
	done
