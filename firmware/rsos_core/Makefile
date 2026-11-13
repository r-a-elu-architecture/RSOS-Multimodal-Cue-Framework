CXX ?= g++
CXXFLAGS ?= -std=c++11 -O2 -Wall -Wextra -Werror
all: host_sim module_sim
host_sim: host_sim.cpp rsos_core.cpp rsos_core.h
	$(CXX) $(CXXFLAGS) -o $@ host_sim.cpp rsos_core.cpp
module_sim: module_sim.cpp rsos_modules.cpp rsos_modules.h
	$(CXX) $(CXXFLAGS) -o $@ module_sim.cpp rsos_modules.cpp -lm
clean:
	rm -f host_sim module_sim
