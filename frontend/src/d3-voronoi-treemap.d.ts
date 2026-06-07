// Minimal ambient types for d3-voronoi-treemap, which ships no type definitions.
declare module "d3-voronoi-treemap" {
  import type { HierarchyNode } from "d3-hierarchy";

  export interface VoronoiTreemap {
    <T>(root: HierarchyNode<T>): void;
    clip(polygon: [number, number][]): VoronoiTreemap;
    convergenceRatio(ratio: number): VoronoiTreemap;
    maxIterationCount(count: number): VoronoiTreemap;
    minWeightRatio(ratio: number): VoronoiTreemap;
    prng(rng: () => number): VoronoiTreemap;
  }

  export function voronoiTreemap(): VoronoiTreemap;
}
