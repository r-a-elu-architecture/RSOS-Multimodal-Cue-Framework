CXX ?= g++
CXXFLAGS ?= -std=c++11 -O2 -Wall -Wextra -Werror
all: host_sim module_sim link_test
host_sim: host_sim.cpp rsos_core.cpp rsos_core.h
	$(CXX) $(CXXFLAGS) -o $@ host_sim.cpp rsos_core.cpp
module_sim: module_sim.cpp rsos_modules.cpp rsos_modules.h
	$(CXX) $(CXXFLAGS) -o $@ module_sim.cpp rsos_modules.cpp -lm
link_test: link_test.cpp rsos_link.cpp rsos_link.h
	$(CXX) $(CXXFLAGS) -o $@ link_test.cpp rsos_link.cpp
clean:
	rm -f host_sim module_sim link_test
