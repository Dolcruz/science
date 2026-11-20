// Local search for digit alphabets (A1)-(A3) in Gaussian base beta = U + iV.
// usage: search U V Rc seconds seed [initfile]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

typedef struct { int *a; int n, cap; } vec;
static void vpush(vec *v, int x){ if(v->n==v->cap){ v->cap=v->cap?2*v->cap:8; v->a=realloc(v->a,sizeof(int)*v->cap);} v->a[v->n++]=x; }

static int U,V,N,M; static double Rc;
static int *px,*py; static int *resid; // residue index 0..N-1 (unique code)
static int *grid; static int G0, GW; // map coordinates -> candidate idx
static int *T; static long nT; // triangles a,b,c
static vec *tri_of; // per candidate: triangle ids
static int *F; static long nF; // forbidden triples (distinct-ish) store 3 ids
static vec *forb_of;
static vec *res_of; // candidates per residue

static uint64_t rng=88172645463325252ULL;
static inline uint64_t xr(){ rng^=rng<<13; rng^=rng>>7; rng^=rng<<17; return rng; }
static inline double ur(){ return (xr()>>11)*(1.0/9007199254740992.0); }

static int cid(int x,int y){ int X=x+G0, Y=y+G0; if(X<0||Y<0||X>=GW||Y>=GW) return -1; return grid[X*GW+Y]; }
static int rescode(long x,long y){ long a=((long)U*x+(long)V*y)%N; if(a<0)a+=N; long b=((long)U*y-(long)V*x)%N; if(b<0)b+=N; // for N with gcd structure, pair is unique code; map to a*N+b hashed
  return (int)(a*N+b); }

// hash residue codes to compact ids
#include <search.h>
static int *rc_keys; static int nrc=0;
static int *rc_table; static int rc_size;
static int rc_id(int code){ unsigned h=(unsigned)code*2654435761u; int i=h%rc_size; while(rc_table[i]!=-1){ if(rc_keys[rc_table[i]]==code) return rc_table[i]; i=(i+1)%rc_size;} rc_keys[nrc]=code; rc_table[i]=nrc; return nrc++; }
static int rc_find(int code){ unsigned h=(unsigned)code*2654435761u; int i=h%rc_size; while(rc_table[i]!=-1){ if(rc_keys[rc_table[i]]==code) return rc_table[i]; i=(i+1)%rc_size;} return -1; }

// state
static char *in; static int *members; static int *mpos; static int q=0;
static int *cnt; // scratch
static int *queue;

static vec *act;
static void vdel(vec *v,int t){ for(int j=0;j<v->n;j++) if(v->a[j]==t){ v->a[j]=v->a[--v->n]; return; } }
static void add(int x){ in[x]=1; mpos[x]=q; members[q++]=x; vec *L=&tri_of[x]; for(int j=0;j<L->n;j++){ int t=L->a[j]; int a=T[3*t],b=T[3*t+1],c=T[3*t+2]; if(in[a]&&in[b]&&in[c]){ vpush(&act[a],t); vpush(&act[b],t); vpush(&act[c],t);} } }
static void rem(int x){ vec *L=&act[x]; for(int j=0;j<L->n;j++){ int t=L->a[j]; for(int r=0;r<3;r++){ int y=T[3*t+r]; if(y!=x) vdel(&act[y],t);} } L->n=0; in[x]=0; int p=mpos[x]; int y=members[--q]; members[p]=y; mpos[y]=p; }

// compute core: returns size, marks core in corem
static char *corem; static int *corelist; static int ncore;
static char *rmv;
static int peel(int record){ // returns number peeled; queue holds order
  for(int k=0;k<q;k++){ int x=members[k]; cnt[x]=0; corem[x]=0; rmv[x]=0; }
  for(int k=0;k<q;k++){ int b=members[k]; vec *L=&act[b]; for(int j=0;j<L->n;j++){ int t=L->a[j]; if(T[3*t+1]==b) cnt[b]++; } }
  int h=0,tl=0; for(int k=0;k<q;k++){ int x=members[k]; if(cnt[x]==0){ queue[tl++]=x; corem[x]=1; } }
  while(h<tl){ int x=queue[h++]; rmv[x]=1; vec *L=&act[x]; for(int j=0;j<L->n;j++){ int t=L->a[j]; int a=T[3*t],b=T[3*t+1],c=T[3*t+2]; if(b==x) continue; if(!in[a]||!in[b]||!in[c]) continue;
      int other=(a==x)?c:a; if(rmv[other]||rmv[b]) continue; cnt[b]--; if(cnt[b]==0&&!corem[b]){ corem[b]=1; queue[tl++]=b; } } }
  return tl;
}
static int compute_core(){ int tl=peel(0); ncore=0; for(int k=0;k<q;k++){ int x=members[k]; if(!corem[x]) corelist[ncore++]=x; corem[x]=0; } return ncore; }
static char *subm; static int *scnt; static int *sq2;
// core of subset given by list (members of S); returns core size, leaves list of core in out
static int core_sub(int *lst,int n,int *out){
  for(int k=0;k<n;k++){ subm[lst[k]]=1; scnt[lst[k]]=0; }
  for(int k=0;k<n;k++){ int b=lst[k]; vec *L=&act[b]; for(int j=0;j<L->n;j++){ int t=L->a[j]; if(T[3*t+1]==b && subm[T[3*t]] && subm[T[3*t+2]]) scnt[b]++; } }
  int h=0,tl=0; for(int k=0;k<n;k++){ int x=lst[k]; if(scnt[x]==0){ sq2[tl++]=x; subm[x]=2; } }
  while(h<tl){ int x=sq2[h++]; subm[x]=3; vec *L=&act[x]; for(int j=0;j<L->n;j++){ int t=L->a[j]; int a=T[3*t],b=T[3*t+1],c=T[3*t+2]; if(b==x) continue; int other=(a==x)?c:a;
      if(subm[other]==0||subm[other]==3||subm[b]==0||subm[b]==3) continue; if(subm[b]==2) { scnt[b]--; continue; } scnt[b]--; if(scnt[b]==0){ subm[b]=2; sq2[tl++]=b; } } }
  int nc=0; for(int k=0;k<n;k++){ int x=lst[k]; if(subm[x]==1) out[nc++]=x; subm[x]=0; }
  return nc;
}
static int conflicts_forb(int x, int *out){ // returns forbidden triples with x where others in S; out pairs
  int n=0; vec *L=&forb_of[x]; for(int j=0;j<L->n;j++){ int f=L->a[j]; int u0=F[3*f],u1=F[3*f+1],u2=F[3*f+2]; int ok=1; int oth[3],no=0; int ids[3]={u0,u1,u2}; for(int r=0;r<3;r++){ if(ids[r]==x) continue; if(!in[ids[r]]){ok=0;break;} oth[no++]=ids[r]; } if(ok){ out[2*n]=oth[0]; out[2*n+1]=(no>1)?oth[1]:oth[0]; n++; } }
  return n;
}

static void save(const char *fn, int *set, int n){
  // compute peeling order: peel S fully
  FILE *f=fopen(fn,"w"); fprintf(f,"%d %d\n",U,V);
  // rebuild in[] for set
  char *saved=malloc(M); memcpy(saved,in,M); int *sm=malloc(sizeof(int)*M); int sq=q; memcpy(sm,members,sizeof(int)*q);
  while(q>0) rem(members[q-1]); for(int k=0;k<n;k++) add(set[k]);
  int tl=peel(1);
  for(int k=0;k<tl;k++) fprintf(f,"%d %d\n",px[queue[k]],py[queue[k]]);
  fclose(f);
  for(int k=0;k<q;k++) corem[members[k]]=0;
  while(q>0) rem(members[q-1]); for(int k=0;k<sq;k++) add(sm[k]); free(saved); free(sm);
}

int main(int argc,char**argv){
  U=atoi(argv[1]); V=atoi(argv[2]); Rc=atof(argv[3]); double secs=atof(argv[4]); rng^=(uint64_t)atoll(argv[5])*0x9E3779B97F4A7C15ULL; for(int i=0;i<10;i++) xr();
  N=U*U+V*V; int R=(int)ceil(Rc)+1; G0=R; GW=2*R+1; grid=malloc(sizeof(int)*GW*GW); for(int i=0;i<GW*GW;i++) grid[i]=-1;
  px=malloc(sizeof(int)*GW*GW); py=malloc(sizeof(int)*GW*GW); M=0;
  for(int x=-R;x<=R;x++) for(int y=-R;y<=R;y++) if(x*x+y*y<=Rc*Rc){ px[M]=x; py[M]=y; grid[(x+G0)*GW+(y+G0)]=M; M++; }
  rc_size=4*M+7; rc_table=malloc(sizeof(int)*rc_size); for(int i=0;i<rc_size;i++) rc_table[i]=-1; rc_keys=malloc(sizeof(int)*rc_size);
  resid=malloc(sizeof(int)*M); for(int k=0;k<M;k++) resid[k]=rc_id(rescode(px[k],py[k]));
  res_of=calloc(nrc+1,sizeof(vec)); for(int k=0;k<M;k++) vpush(&res_of[resid[k]],k);
  tri_of=calloc(M,sizeof(vec)); forb_of=calloc(M,sizeof(vec));
  long capT=1<<20; T=malloc(sizeof(int)*3*capT); nT=0; long capF=1<<20; F=malloc(sizeof(int)*3*capF); nF=0;
  for(int b=0;b<M;b++) for(int a=0;a<M;a++){ if(a==b) continue; int cx=px[b]-(py[a]-py[b]), cy=py[b]+(px[a]-px[b]); int c=cid(cx,cy); if(c<0) continue; if(nT==capT){capT*=2; T=realloc(T,sizeof(int)*3*capT);} T[3*nT]=a;T[3*nT+1]=b;T[3*nT+2]=c; vpush(&tri_of[a],nT); vpush(&tri_of[b],nT); vpush(&tri_of[c],nT); nT++; }
  for(int b=0;b<M;b++) for(int c=0;c<M;c++){ long tx=px[b]-py[b]+py[c], ty=px[b]+py[b]-px[c]; int r=rc_find(rescode(tx,ty)); if(r<0) continue; vec *L=&res_of[r]; for(int j=0;j<L->n;j++){ int a=L->a[j]; if(px[a]==tx&&py[a]==ty) continue; if(a==b && b==c) continue; if(a==b||b==c||a==c) continue; // pairs handled by A1 (N odd); keep generic triples
        if(nF==capF){capF*=2; F=realloc(F,sizeof(int)*3*capF);} F[3*nF]=a;F[3*nF+1]=b;F[3*nF+2]=c; vpush(&forb_of[a],nF); vpush(&forb_of[b],nF); vpush(&forb_of[c],nF); nF++; } }
  fprintf(stderr,"N=%d M=%d residues=%d triangles=%ld forbidden=%ld target q>%.1f\n",N,M,nrc,nT,nF,pow(N,0.6722314056));
  act=calloc(M,sizeof(vec)); in=calloc(M,1); members=malloc(sizeof(int)*M); mpos=malloc(sizeof(int)*M); cnt=malloc(sizeof(int)*M); queue=malloc(sizeof(int)*M); corem=calloc(M,1); rmv=calloc(M,1); corelist=malloc(sizeof(int)*M); subm=calloc(M,1); scnt=malloc(sizeof(int)*M); sq2=malloc(sizeof(int)*M);
  int *conf=malloc(sizeof(int)*2*4000000);
  if(argc>6){ FILE *f=fopen(argv[6],"r"); int x,y; int first=1; while(fscanf(f,"%d %d",&x,&y)==2){ if(first){first=0; continue;} int k=cid(x,y); if(k>=0&&!in[k]) add(k);} fclose(f); fprintf(stderr,"init q=%d core=%d\n",q,compute_core()); }
  int best=q; int *bestset=malloc(sizeof(int)*M); memcpy(bestset,members,sizeof(int)*q);
  int *undo_rm=malloc(sizeof(int)*M); int nrm; int *cl=malloc(sizeof(int)*M); int *tmpc=malloc(sizeof(int)*M); int *tmpl=malloc(sizeof(int)*M); int *tmpo=malloc(sizeof(int)*M);
  clock_t t0=clock(); long it=0, acc=0; double Temp=0.6; double T0=(argc>7)?atof(argv[7]):0.5;
  char fn[256]; sprintf(fn,"best_%d_%d_R%g.alpha",U,V,Rc); double lastsave=0;
  while(1){
    it++; if((it&255)==0){ double el=(double)(clock()-t0)/CLOCKS_PER_SEC; if(el>secs) break; Temp=T0*(1-el/secs)+0.02; if(el-lastsave>5 && best>0){ lastsave=el; } }
    int x=xr()%M; if(in[x]) continue;
    nrm=0;
    vec *L=&res_of[resid[x]]; for(int j=0;j<L->n;j++){ int y=L->a[j]; if(in[y]){ rem(y); undo_rm[nrm++]=y; } }
    int nc=conflicts_forb(x,conf); for(int k=0;k<nc;k++){ int y0=conf[2*k],y1=conf[2*k+1]; if(in[y0]&&in[y1]){ int y=(xr()&1)?y0:y1; rem(y); undo_rm[nrm++]=y; } }
    if(nrm>3){ for(int k=0;k<nrm;k++) add(undo_rm[k]); continue; }
    add(x);
    int ok=1;
    int nco=compute_core(); memcpy(cl,corelist,sizeof(int)*nco);
    while(nco>0){
      if(nrm>=3){ ok=0; break; }
      int *cand=tmpc; int nca=0; for(int k=0;k<nco;k++) if(cl[k]!=x) cand[nca++]=cl[k];
      if(nca==0){ ok=0; break; }
      for(int k=nca-1;k>0;k--){ int r=xr()%(k+1); int tmp=cand[k]; cand[k]=cand[r]; cand[r]=tmp; }
      int found=-1; int tries=nca<60?nca:60; int bestsz=1<<30, besty=cand[0];
      for(int k=0;k<tries;k++){ int y=cand[k]; int m=0; for(int z=0;z<nco;z++) if(cl[z]!=y) tmpl[m++]=cl[z]; int cs=core_sub(tmpl,m,tmpo); if(cs<bestsz){bestsz=cs; besty=y;} if(cs==0){ found=y; break; } }
      int y=besty; rem(y); undo_rm[nrm++]=y;
      int m=0; for(int z=0;z<nco;z++) if(cl[z]!=y) tmpl[m++]=cl[z]; nco=core_sub(tmpl,m,cl);
    }
    int delta = 1 - nrm;
    if(ok && (delta>=0 || ur()<exp(delta/Temp))){
      acc++;
      if(q>best){ best=q; memcpy(bestset,members,sizeof(int)*q); save(fn,bestset,best); fprintf(stderr,"it=%ld q=%d alpha=%.6f T=%.3f\n",it,q,2*log(q)/log(N),Temp); }
    } else { rem(x); for(int k=0;k<nrm;k++) add(undo_rm[k]); }
  }
  fprintf(stderr,"acc=%ld\n",acc);
  printf("%d %d best=%d alpha=%.8f it=%ld final q=%d\n",U,V,best,2*log(best)/log(N),it,q);
  return 0;
}
