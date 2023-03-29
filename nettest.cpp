#include<bits/stdc++.h>
#include <cctype>
#include <fstream>
#include <string>
using namespace std;
using ll=long long;
#define endl "\n"
#define dd(x) cerr<<#x<<" = "<<x<<" ";
#define de(x) cerr<<#x<<" = "<<x<<endl;

bool global_test_flag=1;

void prasestring1(string &s,vector<string>&out){
	string p;
	int once=0;
	int i=0;
	while(i<(int)s.size()&&s[i]==' ')
		i++;
	for(;i<(int)s.size();++i){
		if(i>0&&s[i]==s[i-1]&&s[i]==' ')continue;
		if(s[i]=='|'||s[i]==' '){
			if(p.size()<=1){
				p.clear();
				continue;
			}
			if(once<1)
				once++;
			else 
				out.push_back(p);
			p.clear();
			continue;
		}
		p+=s[i];
	}
	out.push_back(p);
}

vector<string>interface,bytesdes;
vector<vector<ll> >recvs,trans;

vector<string> preblacklist={"lo","docker","utun","tunnel"};

bool isrealdev(string &s){
	for(auto &i:preblacklist){
		bool checked=true;
		if(i.size()>s.size())continue;
		for(int j=0;j<i.size()&&checked;++j){
			if(i[j]!=s[j])checked=false;	
		}
		if(checked) return false;
	}
	return true;
}

bool prasestring2(string &s,vector<ll> &recv,vector<ll> &tran,size_t siz){
	string dev;
	bool calloncecheck=1;
	int i,j;
	ll tmp=0;
	for(i=0;i<(int)s.size();++i){
		if(s[i]==':') break;
		if(s[i]==' ') continue;
		dev+=s[i];
	}
	if(isrealdev(dev)==false) return false;
	interface.push_back(dev);
	j=0;
	while(i<s.size()&&!isdigit(s[i]))i++;
	for(;i<s.size()&&j<siz-siz/2;++i){
		if(i>0&&s[i]==s[i-1]&&!isdigit(s[i]))continue;
		if(!isdigit(s[i])){
			recv.push_back(tmp);
			tmp=0;
			j++;
			continue;
		}
		tmp=tmp*10+s[i]-'0';
		if(tmp>INT_MAX&&calloncecheck){
			cerr<<"Warning: tmp > INT_MAX, tmp:"<<tmp<<endl;
			calloncecheck=1;
		}
	}
	j=0;
	for(i=i+1;i<s.size()&&j<siz/2;++i){
    	if(i>0&&s[i]==s[i-1]&&!isdigit(s[i]))continue;
		if(s[i]==' '){
            tran.push_back(tmp);
            tmp=0;
            j++;
		 	continue;
        }
        tmp=tmp*10+s[i]-'0';
        if(tmp>INT_MAX&&calloncecheck){
            cerr<<"Warning: tmp > INT_MAX, tmp:"<<tmp<<endl;
            calloncecheck=1;
        }
    }
	tran.push_back(tmp);
	return 1;
}

int getinterface(std::ofstream &os){
	const string path="cat /proc/net/dev > ./interface.tmp";
	vector<string>s;
	vector<ll>recv,tran;
	string p;
	int successinterface_test=0,failinterface_test=0;

	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		return 1;
	}

	std::ifstream ints("interface.tmp", std::ios::binary);
	
	getline(ints,p);
	getline(ints,p);
	prasestring1(p,s);
	while(getline(ints,p)){
		int ret=prasestring2(p,recv,tran,s.size());
		if(ret==0)continue;
		recvs.push_back(recv);
		trans.push_back(tran);
		recv.clear();
		tran.clear();
	}
	swap(bytesdes,s);
	for(int i=0;i<(int)interface.size();++i){
		cout<<interface[i]<<endl;
		int j;
		for(j=0;j<bytesdes.size()-bytesdes.size()/2;++j)
		cout<<bytesdes[j]<<" ";
		cout<<endl;
		int errs=0,drop=0;
		for(int k=0;k<recvs[i].size();++k){
			cout<<recvs[i][k]<<" ";
			if(bytesdes[k]=="errs"&&recvs[i][k]>0){
				errs=recvs[i][k];
			}
		}
		cout<<endl;
		if(errs){
			os<<"Failed interface recv test: "<<interface[i]<<endl;
			os<<"recvs errs in "<<interface[i]<<", count: "<<errs<<endl;
			failinterface_test++;
			global_test_flag=false;
		}
		else {
			os<<"Passed interface recv test: "<<interface[i]<<endl;
			successinterface_test++;
		}
		for(;j<bytesdes.size();++j){
			cout<<bytesdes[j]<<" ";
		}
		cout<<endl;
		errs=0,drop=0;
		for(int k=0;k<trans[i].size();++k){
			cout<<trans[i][k]<<" ";
			if(bytesdes[k+recvs[i].size()]=="errs"&&trans[i][k]>0){
				errs=trans[i][k];
			}
		}
		cout<<endl;
		if(errs){
			os<<"Failed interface tran test: "<<interface[i]<<endl;
			os<<"tran errs in "<<interface[i]<<", count: "<<errs<<endl;
			failinterface_test++;
		}
		else {
			os<<"Passed interface tran test: "<<interface[i]<<endl;
			successinterface_test++;
		}
	}
	if(successinterface_test>=0&&failinterface_test==0){

		if(successinterface_test>=2){
			os<<"Passed the interface test, the interface count is "<<successinterface_test/2<<"."<<endl;
		}
		else{
			os<<"Warning the computer has none network interface."<<endl;
		}

		return 0;
	}
	else{
		os<<"Failed the interface test."<<endl;
		return 1;
	}
}

map<string,string> int2driver;// interface to driver;
set<string> driverset;
int getdriver(std::ofstream& os){// stat --format '%N' /sys/class/net/*/device/driver 拿到driver
	for(const auto &s:interface){
		const string filename="getdriver.tmp";
		const string path="stat --format '%N' /sys/class/net/"+s+"/device/driver > "+filename;
		if(system(path.c_str())!=0){
			os<<"Failed execute system command :"<<path<<endl;
			return 1;
		}
		std::ifstream ints(filename, std::ios::binary);
		string p;
		getline(ints,p);
		if(p.size()<=2){
			os<<"Failed get driver int the interface: "<<s<<endl;
			return 1;
		}
		string dri;
		for(int i=p.size()-2;i>=0;i--){
			if(p[i]=='/') break;
			dri+=p[i];
		}
		reverse(dri.begin(),dri.end());
		driverset.insert(dri);
		int2driver[s]=dri;
		cout<<"Find interface:"<<s<<" "<<"matched driver:"<<dri<<endl;
	}
	return 0;
}

int ethtool_i(std::ofstream& os,const string& s){ // ethtool -i 对应接口拿到driver版本信息和支持的一些特性 
	const string filename="ethtool_"+s+"_info.txt";
	const string path="ethtool -i "+s+" > "+filename;

	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		return 1;
	}

	std::ifstream ints(filename, std::ios::binary);
	string p;
	getline(ints,p);
	string dri;
	int i;
	for(i=0;i<p.size();++i)if(p[i]==':') break;
	if(i==p.size()) {
		os<<"Failed find driver in the interface: "<<s<<endl;
		return 1;
	}
	return 0;
}

int ethtool_k(std::ofstream& os,const string& s){ // ethtool -k 对应接口拿到支持特性清单
	const string filename="ethtool_"+s+"_feat.txt";
	const string path="ethtool -k "+s+" > "+" ethtool_"+filename;

	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		return 1;
	}

	return 0;
}

inline bool iserr(string& s){// err or error
	if(s.find("err")!=string::npos){
		return true;
	}
	if(s.find("error")!=string::npos){
		return true;
	}
	return false;
}

int ethtool_S(std::ofstream& os,const string& s){ // ethtool -S 对应接口拿到 接口状态
	const string filename="ethtool_"+s+"_stat.txt";
	const string path="ethtool -S "+s+" > "+" ethtool_"+filename;
	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		return 1;
	}
	
	std::ifstream ints(filename, std::ios::binary);
	string p;
	int check=1;
	while(getline(ints,p)){// err or error
		int err=iserr(p),i;
		if(err){
			for(i=0;i<p.size();++i) if(p[i]==':') break;
			i++;
			long long count=0;
			for(;i<p.size();++i){
				if(isdigit(p[i]))
				count=count*10+p[i]-'0';
			}
			if(count){
				os<<"interface "<<s<<" has errs: "<<p<<endl;
				check=0;
			}
		}
	}
	return !(check==1);
}

int ethtool_d(std::ofstream& os,const string& s){ // ethtool -d 对应接口拿到寄存器信息(如果驱动支持且有特权sudo)
	const string filename="ethtool_"+s+"_reg.txt";
	const string path="sudo ethtool -d "+s+" > "+" ethtool_"+filename;
	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		os<<"Driver not support or not as root?"<<endl;
		return 1;
	}
	return 0;
}

int ethtool_t(std::ofstream& os,const string& s){ // ethtool -t 对应接口调用驱动自测逻辑(如果驱动支持且有特权sudo)
	const string filename="ethtool_"+s+"_test.txt";
	const string path="sudo ethtool -t "+s+" > "+" ethtool_"+filename;
	if(system(path.c_str())!=0){
		os<<"Failed execute system command :"<<path<<endl;
		os<<"Driver not support or not as root?"<<endl;
		return 1;
	}
	return 0;
}

int ethtool_test(std::ofstream &os){
	os<<"Count interface: "<<interface.size()<<" ."<<endl;
	int flag = 0;
	for(auto &i:interface){
		flag|=ethtool_i(os, i);
		flag|=ethtool_k(os, i);
		flag|=ethtool_S(os, i);
		ethtool_d(os, i);
		ethtool_t(os, i);
	}
	if(flag==0){
		os<<"Passed the ethtool test."<<endl;
	}
	else{
		os<<"Failed the ethtool test."<<endl;
	}
	return !(flag==0);
}

int kernellog_test(std::ofstream &os){
	int kernellog_test_check=1;
	{
		const string filename="kernelmsg_err.txt";
		const string path="sudo dmesg -l 3 >"+filename;
		if(system(path.c_str())!=0){
			os<<"Failed execute system command :"<<path<<endl;
			os<<"Driver not support or not as root?"<<endl;
			return 1;
		}	
		std::ifstream ints(filename, std::ios::binary);
		string p;
		int check=1;
		while(getline(ints,p)){
			for(auto &i:driverset){
				if(p.find(i)!=string::npos){
					check=0;
					cerr<<"Found errs: "<<p<<endl;
				}
			}
		}
		if(check==1){
			cout<<"kernel log has no net driver errors"<<endl;
		}
		else {
			kernellog_test_check=0;
		}
	}
	{
		const string filename="kernelmsg_warn.txt";
		const string path="sudo dmesg -l 4 >"+filename;
		if(system(path.c_str())!=0){
			os<<"Failed execute system command :"<<path<<endl;
			os<<"Driver not support or not as root?"<<endl;
			return 1;
		}	
		std::ifstream ints(filename, std::ios::binary);
		string p;
		int check=1;
		while(getline(ints,p)){
			for(auto &i:driverset){
				if(p.find(i)!=string::npos){
					check=0;
					cerr<<"Found errs: "<<p<<endl;
				}
			}
		}
		if(check==1){
			cout<<"kernel log has no net driver warnings"<<endl;
		}
		else {
			kernellog_test_check=0;
		}
	}
	if(kernellog_test_check==0){
		os<<"Failed kernel log test, check err."<<endl;
		return 2;
	}
	else{
		os<<"Passed kernel log test, has no driver err or warning log or may dmesg buffer overflow."<<endl;
	}
	return 0;
}

int main(){
	global_test_flag=true;
	string s="networktest.txt";
	std::ofstream os(s, std::ios::binary);
	
	int ret=getinterface(os);
	
	if(ret){
		global_test_flag=false;
	}
	
	ret=getdriver(os);

	if(ret){
		global_test_flag=false;
	}
	
	ret=ethtool_test(os);

	if(ret){
		global_test_flag=false;
	}

	if(kernellog_test(os)==2){
		global_test_flag=false;
	}

	if(global_test_flag==true)
	os<<"All Tests Passed"<<endl;
}
