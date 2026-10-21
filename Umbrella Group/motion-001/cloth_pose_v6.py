"""Shot-local pleat packing; canonical open geometry/UV/print are unchanged."""

def install(geometry):
    if getattr(geometry,'_v6_drape_installed',False):
        return
    # Fewer, broader folds use the source's own area-constrained packing solver.
    # No random displacement is added to a nearly collapsed cloth surface.
    geometry.CONFIG['folds_per_gore']=4
    geometry._v6_drape_installed=True
