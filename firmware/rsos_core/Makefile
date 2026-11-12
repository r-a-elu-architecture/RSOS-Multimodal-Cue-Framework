CXX ?= g++
CXXFLAGS ?= -std=c++11 -O2 -Wall -Wextra -Werror
host_sim: host_sim.cpp rsos_core.cpp rsos_core.h
	$(CXX) $(CXXFLAGS) -o $@ host_sim.cpp rsos_core.cpp
clean:
	rm -f host_sim
