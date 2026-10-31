/*
MIT License

Copyright (c) 2021 LDPGraphStatistics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Test harness generated from the two upstream functions, unmodified.
Only the sampler and allocation helpers are replaced to inject a fixed noise tape.
This validates formulas, not the upstream RNG.
*/

#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
using namespace std;
int NodeNum,NSType=2;
double Eps=2,EpsNsMaxDeg=.4;
namespace stats {
using rand_engine_t=int;
vector<double> tape;
size_t pos=0;
double rlaplace(double loc,double scale,rand_engine_t&) { return loc+scale*tape.at(pos++); }
}
stats::rand_engine_t engine;
template<class T> void malloc1D(T** p,int n){*p=new T[n];}
template<class T> void free1D(T* p){delete[] p;}
double CalcNSMaxDeg(int *deg, int &max_deg, double eps, string outfile){
	double *deg_lap;
	double max_deg_ns;
	int i;
	FILE *fp;

	// Initialization
	malloc1D(&deg_lap, NodeNum);

	// Calculate the max of Deg and Deg+Lap(eps) --> max_deg, max_deg_ns
	max_deg = 0;
	max_deg_ns = 0.0;
	for(i=0;i<NodeNum;i++){
		deg_lap[i] = (double)deg[i] + stats::rlaplace(0.0, 1.0/eps, engine);
		if(max_deg < deg[i]) max_deg = deg[i];
		if(max_deg_ns < deg_lap[i]) max_deg_ns = deg_lap[i];
	}

	// If max_deg_ns exceeds NodeNum - 1, then use NodeNum - 1
	if(max_deg_ns > (double)NodeNum - 1.0) max_deg_ns = (double)NodeNum - 1.0;

	// free
	free1D(deg_lap);

	return max_deg_ns;
}

void CalcNLocSt(long long st2_num, long long st3_num, int *deg, string outfile, double &st2_num_ns, double &st3_num_ns, double &sen_st2, double &sen_st3){
	int glb_max_deg;
	int max_deg;
	int sen_st2_ij, sen_st3_ij;
	double EpsLap;
	double max_deg_ns;
	int max_deg_ns_floor;
	int del_num;
	int *rndperm;
	int i, j, x;
	FILE *fp;

    // Initialization
    st2_num_ns = st2_num;
    st3_num_ns = st3_num;

    // Lap (#nodes)
    if(NSType == 0){
		// Global sensitivity using #nodes --> sen_st2, sen_st3
        glb_max_deg = NodeNum - 1;
        sen_st2 = (double)glb_max_deg;
        sen_st3 = (double)glb_max_deg * ((double)glb_max_deg - 1.0) / 2.0;

		// Add Lap for each user
		for(i=0;i<NodeNum;i++){
			// Add Lap(sen_st2/Eps) --> st2_num_ns
			st2_num_ns += stats::rlaplace(0.0, sen_st2/Eps, engine);
			// Add Lap(sen_st3/Eps) --> st3_num_ns
			st3_num_ns += stats::rlaplace(0.0, sen_st3/Eps, engine);
		}
	}
	// Lap (max degree)
	else if(NSType == 1){
        // Global sensitivity using max degree --> sen_st2, sen_st3
        sen_st2 = sen_st3 = 0;
		// max(deg) --> max_deg
		max_deg = 0;
		for(i=0;i<NodeNum;i++){
			if(max_deg < deg[i]) max_deg = deg[i];
		}
		sen_st2 = (double)max_deg;
		sen_st3 = (double)max_deg * ((double)max_deg - 1.0) / 2.0;

		// Add Lap for each user
		for(i=0;i<NodeNum;i++){
			// Add Lap(sen_st2/Eps) --> st2_num_ns
			st2_num_ns += stats::rlaplace(0.0, sen_st2/Eps, engine);
			// Add Lap(sen_st3/Eps) --> st3_num_ns
			st3_num_ns += stats::rlaplace(0.0, sen_st3/Eps, engine);
		}
	}
	// Lap (noisy max degree)
	else{
		// Eps = EpsNsMaxDeg + EpsLap
		EpsLap = Eps - EpsNsMaxDeg;
		// Calculate the noisy max degree --> max_deg_ns
		max_deg_ns = CalcNSMaxDeg(deg, max_deg, EpsNsMaxDeg, outfile);

		// If max(deg) exceeds max_deg_ns, then perform graph projection
		if((double)max_deg > max_deg_ns){
			max_deg_ns_floor = (int)floor(max_deg_ns);
			del_num = 0;
			// Calculate #2-stars, #3-stars again --> st2_num_ns, st3_num_ns
			st2_num_ns = st3_num_ns = 0;
			for(i=0;i<NodeNum;i++){
				if(deg[i] <= max_deg_ns_floor){
					st2_num_ns += ((long long)deg[i] * ((long long)deg[i]-1)) / 2;
					st3_num_ns += ((long long)deg[i] * ((long long)deg[i]-1) * ((long long)deg[i]-2)) / 6;
				}
				else{
					st2_num_ns += ((long long)max_deg_ns_floor * ((long long)max_deg_ns_floor-1)) / 2;
					st3_num_ns += ((long long)max_deg_ns_floor * ((long long)max_deg_ns_floor-1) * ((long long)max_deg_ns_floor-2)) / 6;
					del_num += (deg[i] - max_deg_ns_floor);
				}
			}
		}

        // Global sensitivity using noisy max degree --> sen_st2, sen_st3
        sen_st2 = max_deg_ns;
        sen_st3 = max_deg_ns * (max_deg_ns - 1.0) / 2.0;

		// Add Lap for each user
		for(i=0;i<NodeNum;i++){
			// Add Lap(sen_st2/Eps) --> st2_num_ns
			st2_num_ns += stats::rlaplace(0.0, sen_st2/EpsLap, engine);
			// Add Lap(sen_st3/Eps) --> st3_num_ns
			st3_num_ns += stats::rlaplace(0.0, sen_st3/EpsLap, engine);
		}
	}
}


int main(){
cout<<setprecision(17);
int cases;cin>>cases;
for(int c=0;c<cases;c++){
cin>>NodeNum>>EpsNsMaxDeg;
vector<int>d(NodeNum);long long st2=0,st3=0;
for(int&i:d){cin>>i;st2+=(long long)i*(i-1)/2;st3+=(long long)i*(i-1)*(i-2)/6;}
stats::tape.resize(3*NodeNum);stats::pos=0;
for(double&z:stats::tape)cin>>z;
double r2,r3,s2,s3;
CalcNLocSt(st2,st3,d.data(),"",r2,r3,s2,s3);
cout<<r2<<" "<<r3<<" "<<s2<<" "<<s3<<" "<<stats::pos<<"\n";
}
}
