/* Line schedules for a 4 x N grid row (sites (x, z), x < 4, z < N) on a line of n = 4N qubits.
   Operations on neighbouring positions: U (bond in place), SWAP.U (bond riding on a swap), SWAP (empty swap).
   Every bond (x-bonds and z-bonds of the grid) exactly once. Bridge sets: every site must stand at least once on a
   position of each set (one set per row-pair a line takes part in). Depth-first search with a visited hash, over
   random start arrangements (and given ones). Prints the first schedule with at most E empty swaps.
   usage: line_dfs N E tries seed maxnodes "set1" ["set2"]   (a set: comma list of positions) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define MAXN 16
int N, n, E, nb, nsets; int bond_of[MAXN][MAXN]; int setmask[4]; /* position masks */
uint64_t FULLB; int arr[MAXN]; int opk[256], ope[256], nops; long nodes, maxnodes;
#define HS (1u<<24)
uint64_t *hkey; uint8_t *hval;
static uint64_t hashs(int *a, uint64_t m, uint64_t v, int emp) {
  uint64_t h = 1469598103934665603ULL;
  for (int i = 0; i < n; i++) { h ^= a[i]; h *= 1099511628211ULL; }
  h ^= m * 0x9E3779B97F4A7C15ULL; h ^= v * 0xC2B2AE3D27D4EB4FULL + emp; return h | 1;
}
static int seen(uint64_t h) {
  uint32_t i = (uint32_t)(h >> 40) & (HS - 1);
  while (hkey[i]) { if (hkey[i] == h) return 1; i = (i + 1) & (HS - 1); }
  hkey[i] = h; return 0;
}
/* visit bits: site s visited set j -> bit s*nsets + j */
static uint64_t visits(int *a) {
  uint64_t v = 0;
  for (int j = 0; j < nsets; j++) for (int p = 0; p < n; p++) if (setmask[j] >> p & 1) v |= 1ULL << (a[p] * nsets + j);
  return v;
}
uint64_t FULLV;
static int dfs(uint64_t m, uint64_t v, int emp) {
  if (m == FULLB && v == FULLV) return 1;
  if (++nodes > maxnodes) return 0;
  if (seen(hashs(arr, m, v, emp))) return 0;
  for (int e = 0; e < n - 1; e++) {
    int b = bond_of[arr[e]][arr[e + 1]];
    if (b >= 0 && !(m >> b & 1)) {
      /* SWAP.U */
      int t = arr[e]; arr[e] = arr[e + 1]; arr[e + 1] = t;
      opk[nops] = 1; ope[nops++] = e;
      if (dfs(m | 1ULL << b, v | visits(arr), emp)) return 1;
      nops--; t = arr[e]; arr[e] = arr[e + 1]; arr[e + 1] = t;
      /* U in place */
      opk[nops] = 0; ope[nops++] = e;
      if (dfs(m | 1ULL << b, v, emp)) return 1;
      nops--;
    }
  }
  if (emp < E) for (int e = 0; e < n - 1; e++) {
    int t = arr[e]; arr[e] = arr[e + 1]; arr[e + 1] = t;
    opk[nops] = 2; ope[nops++] = e;
    if (dfs(m, v | visits(arr), emp + 1)) return 1;
    nops--; t = arr[e]; arr[e] = arr[e + 1]; arr[e + 1] = t;
  }
  return 0;
}
int main(int argc, char **argv) {
  N = atoi(argv[1]); E = atoi(argv[2]); long tries = atol(argv[3]); srand(atoi(argv[4]));
  maxnodes = atol(argv[5]);
  n = 4 * N; nsets = 0;
  for (int k = 6; k < argc; k++) {
    int msk = 0; char *s = strdup(argv[k]); for (char *t = strtok(s, ","); t; t = strtok(NULL, ",")) msk |= 1 << atoi(t);
    setmask[nsets++] = msk;
  }
  memset(bond_of, -1, sizeof bond_of); nb = 0;
  for (int z = 0; z < N; z++) for (int x = 0; x < 4; x++) {
    int s = x + 4 * z;
    if (x < 3) { bond_of[s][s + 1] = bond_of[s + 1][s] = nb++; }
    if (z < N - 1) { bond_of[s][s + 4] = bond_of[s + 4][s] = nb++; }
  }
  FULLB = (nb == 64) ? ~0ULL : ((1ULL << nb) - 1);
  FULLV = 0; for (int s = 0; s < n; s++) for (int j = 0; j < nsets; j++) FULLV |= 1ULL << (s * nsets + j);
  hkey = calloc(HS, sizeof(uint64_t));
  printf("N %d n %d bonds %d sets %d E %d tries %ld maxnodes %ld\n", N, n, nb, nsets, E, tries, maxnodes);
  for (long tr = 0; tr < tries; tr++) {
    for (int i = 0; i < n; i++) arr[i] = i;
    for (int i = n - 1; i > 0; i--) { int j = rand() % (i + 1); int t = arr[i]; arr[i] = arr[j]; arr[j] = t; }
    int start[MAXN]; memcpy(start, arr, sizeof start);
    memset(hkey, 0, HS * sizeof(uint64_t)); nodes = 0; nops = 0;
    if (dfs(0, visits(arr), 0)) {
      printf("FOUND try %ld nodes %ld ops %d\nstart:", tr, nodes, nops);
      for (int i = 0; i < n; i++) printf(" %d.%d", start[i] % 4, start[i] / 4);
      printf("\nops:");
      for (int i = 0; i < nops; i++) printf(" %s@%d", opk[i] == 0 ? "U" : opk[i] == 1 ? "SU" : "SW", ope[i]);
      printf("\n"); return 0;
    }
  }
  printf("NOT FOUND\n"); return 1;
}
