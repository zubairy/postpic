Changelog of postpic
====================

current master
--------------


**Highlights**

* Add support to read the `Smilei` PIC (https://smileipic.github.io/Smilei/) data format in both cartesian and azimuthal geometry. Postpic uses a build in azimuthal mode expansion very similar to the one used for fbpic.
* To read smilei data, postpic only relies on the hdf5 package and not smilei's happi module for data access. Paricle ID's (ParticleTracking as described by smilei) can be read directly from the hdf5. Happi requires to sort the IDs and write a new hdf5, which can be twice as big as the original dumps. Using postpic's access this step will be skipped and thus access is much faster (but by default with unordered particle IDs as in any other code).


**Incompatible adjustments to previous version**

* `scipy.integrate.simps` has been removed in scipy 1.14. Postpic uses `scipy.integrate.simpson` which has been introduced in scipy 1.6.0 (Dec 31st 2020).


**Other improvements and new features**

* Compatibility with numpy 2.0 and the sanitizer checks of numexpr 2.8.6. ([#281](https://github.com/skuschel/postpic/pull/281) -- [a304e73](https://github.com/skuschel/postpic/commit/a304e7370259b3b09873a998ccc8f6a6c0241b2c))
* New function exporttoh5 to export particle tracks directly into an hdf5 file; updated depracted np.int()-function. ([#291](https://github.com/skuschel/postpic/pull/291))


v0.5
----

2022-10-22

This is the last version with python 2 support. Changes in setuptools (see for example python [PEP 517](https://peps.python.org/pep-0517/) and [PEP 660](https://peps.python.org/pep-0660/) ) require changes in the setup. Backward compatibility will therefore be dropped. Current tests already do not inlcude python2 anymore.


**Highlights**

* Parallelized implementation of `Field.map_coordinates`
* Added support for reading files written by the fbpic v0.13.0 code ( https://github.com/fbpic ). The fields can be accessed by `Er` and `Etheta`, which have been introduced to the fbpic data reader. Particles are saved in Cartesian coordinates, hence the interface does not change there.
* Reimplementation of `Field.fft`, see below.

**Incompatible adjustments to previous version**

* Reimplementation of `Field.fft`. This changes the phases of Fourier transforms in a way to make it more consistent. However, if your code depends on the phases, `Field.fft()` now has a parameter `old_behaviour` that can be used to switch back to the old behaviour.
* Indexing a field by a number (integer or float) will now remove the according axis altogether, instead of leaving behind a length-1 axis.
A new class `KeepDim` was introduced through which the old behaviour can still be used.
Behaviour of PostPic before this change:
```
field.shape == (x,y,z)
field[:, 0.0, :].shape == (x,1,z)
```
Using the new class `KeepDim`, it is possible to retain that behaviour in the new version:
```
field.shape == (x,y,z)
field[:, 0.0, :].shape == (x, z)
field[:, KeepDim(0.0), :].shape == (x,1,z)
```

**Other improvements and new features**

* New convenience method `Field.copy`


v0.4
----

2019-01-14

**Highlights**

* Improved interoperability with numpy:
  * `Field` now understands most of numpy's broadcasting
  * `Field` can be used as an argument to numpy's ufuncs.
* Import and export routines for `Field` incuding vtk, compatible with [paraview](https://www.paraview.org/).
* Coordinate mapping and transform for `Field`.
* Brand new `Multispecies.__call__` interface: This takes an expression, which is evaluated by `numexr`, increasing the speed of per-particle scalar computations strongly. It's also really user-friendly.

**Incompatible adjustments to previous version**
* `postpic.Field` method `exporttocsv` is removed. Use `export` instead.
* `postpic.Field` method `transform` is renamed to `map_coordinates`, matching the underlying scipy-function.
* `postpic.Field` method `mean` has now an interface matching `ndarray.mean`. This means that, if the `axis` argument is not given, it averages across all axes instead the last axis.
* `postpic.Field.map_coordinates` applies now the Jacobian determinant of the transformation, in order to preserve the definite integral.
In your code you will need to turn calls to `Field.transform` into calls to `Field.map_coordinates` and set the keyword argument `preserve_integral=False` to get the old behaviour.
* `postpic.MultiSpecies.createField` has now keyword arguments (`bins`, `shape`), which replace the corresponding entries from the `optargsh` dictionary. The use of the`optargsh` keyword argument has been deprecated.
* The functions `MultiSpecies.compress`, `MultiSpecies.filter`, `MultiSpecies.uncompress` and `ParticleHistory.skip` return a new object now. Before this release, they modified the current object. Assuming  `ms` is a `MultiSpecies` object, the corresponding adjustemens read:<br>
old: `ms.filter('gamma > 2')`<br>
new: `ms = ms.filter('gamma > 2')`
* `plotter_matplotlib` has a new default symmetric colormap

**Other improvements and new features**
* Overload of the `~` (invert) operator on `postpic.MultiSpecies`. If `ms` is a MultiSpecies object with filtered particles (created by the use of `compress` or `filter`), then `~ms` inverts the selection of particles.
* `postpic.Field` has methods `.loadfrom` and `.saveto`. These can be used to save a Field to a ` .npz` file for later use. Use `.loadfrom` to load a Field object from such a file. All attributes of the Field are restored.
* `postpic.Field` has methods `.export` and `.import`. These are used to export fields to and import fields from foreign file formats such as `.csv`, `.vtk`, `.png`, `.tif`, `.jpg`. It is not guaranteed to get all attributes back after `.export`ing and than `.import`ing a Field. Some formats are not available for both methods.
* `postpic` has a new function `time_profile_at_plane` that 'measures' the temporal profile of a pulse while passing through a plane
* `postpic` has a new function `unstagger_fields` that will take a set of staggered fields and returns the fields after removing the stagger
* `postpic` has a new function `export_vector_vtk` that takes up to three fields and exports them as a vector field in the `.vtk` format
* `postpic` has a new function `export_scalars_vtk` that takes up to four fields and exports them as multiple scalar fields on the same grid in the `.vtk` format
* `postpic.Field` works now with all numpy ufuncs, also with `ufunc.reduce`, `ufunc.outer`, `ufunc.accumulate` and `ufunc.at`
* `postpic.Field` now supports broadcasting like numpy arrays, for binary operators as well as binary ufunc operations
* `postpic.Field` has methods `.swapaxes`, `.transpose` and properties `.T` and `ndim` compatible to numpy.ndarray
* `postpic.Field` has methods `all`, `any`, `max`, `min`, `prod`, `sum`, `ptp`, `std`, `var`, `mean`, `clip` compatible to numpy.ndarray
* `postpic.Field` has a new method `map_axis_grid` for transforming the coordinates only along one axis which is simpler than `map_coordinates`, but also takes care of the Jacobian
* `postpic.Field` has a new method `autocutout` used to slice away close-to-zero regions from the borders
* `postpic.Field` has a new method `fft_autopad` used to pad a small number of grid points to each axis such that the dimensions of the Field are favourable to FFTW
* `postpic.Field` has a new method `adjust_stagger_to` to adjust the grid origin to match the grid origin of another field
* `postpic.Field` has a new method `phase` to get the unwrapped phase of the field
* `postpic.Field` has a new method `derivative` to calculate the derivative of a field
* `postpic.Field` has new methods `flip` and `rot90` similar to `np.flip()` and `np.rot90()`
* `postpic.Field.topolar` has new defaults for extent and shape
* `postpic.Field.integrate` now uses the simpson method by default
* `postpic.Field.integrate` now has a new 'fast' method that uses numexpr, suitable for large datasets
* New module `postpic.experimental` to contain experimental algorithms for your reference. These algorithms are not meant to be useable as-is, but may serve as recipes to write your own algorithms.
* k-space reconstruction from EPOCH dumps has greatly improved accuracy due to a new algorithm correctly incorporating the frequency response of the implicit linear interpolation performed by EPOCH's half-steps
* `plotter_matplotlib.plotField` allows to override `aspect` option to `imshow`

v0.3.1
------

2017-10-03

Only internal changes. Versioning is handled by [versioneer](https://github.com/warner/python-versioneer).


v0.3
----

2017-09-28

Many improvements in terms of speed and features. Unfortunately some changes are not backwards-compatible to v0.2.3, so you may have to adapt your code to the new interface. For details, see the corresponding section below.


**Highlights**
* kspace reconstruction and propagation of EM waves.
* `postpic.Field` properly handles operator overloading and slicing. Slicing can be index based (integers) or referring the actual physical extent on the axis of a Field object (using floats).
* Expression based interface to particle properties (see below)

**Incompatible adjustments to previous version**
* New dependency: Postpic requires the `numexpr` package to be installed now.
* Expression based interface of for particles: If `ms` is a `postpic.MultiSpecies` object, then the call `ms.X()` has been deprecated. Use `ms('x')` instead. This new particle interface can handle expressions that the `numexpr` package understands. Also `ms('sqrt(x**2 + gamma - id)')` is valid. This interface is easier to use, has better functionality and is faster due to `numexpr`.
The list of known per particle scalars and their definitions is available at `postpic.particle_scalars`. In addition all constants of `scipy.constants.*` can be used.
In case you find particle scalar that you use regularly which is not in the list, please open an issue and let us know!
* The `postpic.Field` class now behaves more like an `numpy.ndarray` which means that almost all functions return a new field object instead of modifying the current. This change affects the following functions: `half_resolution`, `autoreduce`, `cutout`, `mean`.


**Other improvements and new features**
* `postpic.helper.kspace` can reconstruct the correct k-space from three EM fields provided to distinguish between forward and backward propagating waves (thanks to @Ablinne)
* `postpic.helper.kspace_propagate` will turn the phases in k-space to propagate the EM-wave.
* List of new functions in `postpic` from `postpic.helper` (thanks to @Ablinne): `kspace_epoch_like`, `kspace`, `kspace_propagate`.
* `Field.fft` function for fft optimized with pyfftw (thanks to @Ablinne).
* `Field.__getitem__` to slice a Field object. If integers are provided, it will interpret them as gridpoints. If float are provided they are interpreted as the physical region of the data and slice along the corresponding axis positions (thanks to @Ablinne).
* `Field` class has been massively impoved (thanks to @Ablinne): The operator overloading is now properly implemented and thanks to `__array__` method, it can be interpreted by numpy as an ndarray whenever necessary.
* List of new functions of the `Field` class (thanks to @Ablinne): `meshgrid`, `conj`, `replace_data`, `pad`, `transform`, `squeeze`, `integrate`, `fft`, `shift_grid_by`, `__getitem__`, `__setitem__`, `evaluate`.
* List of new properties of the `Field` class (thanks to @Ablinne): `matrix`, `real`, `imag`, `angle`.
* Many performance optimizations using pyfftw library (optional) or numexpr (now required by postpic) or by avoiding in memory data copying.
* Lots of fixes


v0.2.3
------

2017-02-17

This release brings some bugfixes and various new features.

**Bugfixes**
* Particle property Bz.
* plotting of contourlevels.

**Improvements and new features**
* openPMD support (thanks to @ax3l).
* ParticleHistory class to collect particle information over the entire simulation.
* added particle properties v{x,y,z} and beta{x,y,z}.
* Lots of performance improvemts: particle data will be much less copied in memory now.


v0.2.2 and earlier
------------------

There hasnt been any changelog. Dont use those versions anymore.
