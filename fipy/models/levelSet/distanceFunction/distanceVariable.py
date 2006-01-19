#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "distanceVariable.py"
 #                                    created: 7/29/04 {10:39:23 AM} 
 #                                last update: 12/22/05 {2:38:09 PM}
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2003-11-12 JEG 1.0 original
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

import Numeric
import MA

from fipy.variables.cellVariable import CellVariable
from fipy.tools import numerix

class DistanceVariable(CellVariable):
    r"""
    A `DistanceVariable`
    
    .. raw:: latex

        object calculates $\phi$ so it satisfies,

        $$ | \nabla \phi | = 1 $$

        using the fast marching method with an initial condition defined by
        the zero level set.

    Currently the solution is first order, This suffices for initial
    conditions with straight edges (e.g. trenches in
    electrodeposition). The method should work for unstructured 2D grids
    but testing on unstructured grids is untested thus far. This is a 2D
    implementation as it stands. Extending to 3D should be relatively
    simple.

    Here we will define a few test cases. Firstly a 1D test case

       >>> from fipy.meshes.grid1D import Grid1D
       >>> mesh = Grid1D(dx = .5, nx = 8)
       >>> from distanceVariable import DistanceVariable
       >>> var = DistanceVariable(mesh = mesh, value = (-1, -1, -1, -1, 1, 1, 1, 1))
       >>> var.calcDistanceFunction()
       >>> answer = (-1.75, -1.25, -.75, -0.25, 0.25, 0.75, 1.25, 1.75)
       >>> print var.allclose(answer)
       1

    A 1D test case with very small dimensions.

       >>> dx = 1e-10
       >>> mesh = Grid1D(dx = dx, nx = 8)
       >>> var = DistanceVariable(mesh = mesh, value = (-1, -1, -1, -1, 1, 1, 1, 1))
       >>> var.calcDistanceFunction()
       >>> answer = Numeric.arange(8) * dx - 3.5 * dx
       >>> print var.allclose(answer)
       1

    A 2D test case to test `_calcTrialValue` for a pathological case.

       >>> dx = 1.
       >>> dy = 2.
       >>> from fipy.meshes.grid2D import Grid2D
       >>> mesh = Grid2D(dx = dx, dy = dy, nx = 2, ny = 3)
       >>> var = DistanceVariable(mesh = mesh, value = (-1, 1, 1, 1, -1, 1))
       >>> var.calcDistanceFunction()
       >>> vbl = -dx * dy / Numeric.sqrt(dx**2 + dy**2) / 2.
       >>> vbr = dx / 2
       >>> vml = dy / 2.
       >>> crossProd = dx * dy
       >>> dsq = dx**2 + dy**2
       >>> top = vbr * dx**2 + vml * dy**2
       >>> sqrt = crossProd**2 *(dsq - (vbr - vml)**2)
       >>> sqrt = Numeric.sqrt(max(sqrt, 0))
       >>> vmr = (top + sqrt) / dsq
       >>> answer = (vbl, vbr, vml, vmr, vbl, vbr)
       >>> print var.allclose(answer)
       1

    The `extendVariable` method solves the following equation for a given
    extensionVariable.

    .. raw:: latex

        $$ \nabla u \cdot \nabla \phi = 0 $$

    using the fast marching method with an initial condition defined at
    the zero level set. Essentially the equation solves a fake distance
    function to march out the velocity from the interface.

       >>> from fipy.variables.cellVariable import CellVariable
       >>> mesh = Grid2D(dx = 1., dy = 1., nx = 2, ny = 2)
       >>> var = DistanceVariable(mesh = mesh, value = (-1, 1, 1, 1))
       >>> var.calcDistanceFunction()
       >>> extensionVar = CellVariable(mesh = mesh, value = (-1, .5, 2, -1))
       >>> tmp = 1 / Numeric.sqrt(2)
       >>> print var.allclose((-tmp / 2, 0.5, 0.5, 0.5 + tmp))
       1
       >>> var.extendVariable(extensionVar)
       >>> print extensionVar.allclose((1.25, .5, 2, 1.25))
       1
       >>> mesh = Grid2D(dx = 1., dy = 1., nx = 3, ny = 3)
       >>> var = DistanceVariable(mesh = mesh, value = (-1, 1, 1,
       ...                                               1, 1, 1,
       ...                                               1, 1, 1))
       >>> var.calcDistanceFunction()
       >>> extensionVar = CellVariable(mesh = mesh, value = (-1, .5, -1,
       ...                                                    2, -1, -1,
       ...                                                   -1, -1, -1))

       >>> v1 = 0.5 + tmp
       >>> v2 = 1.5
       >>> tmp1 = (v1 + v2) / 2 + Numeric.sqrt(2. - (v1 - v2)**2) / 2
       >>> tmp2 = tmp1 + 1 / Numeric.sqrt(2)
       >>> print var.allclose((-tmp / 2, 0.5, 1.5, 0.5, 0.5 + tmp, 
       ...                      tmp1, 1.5, tmp1, tmp2))
       1
       >>> answer = (1.25, .5, .5, 2, 1.25, 0.9544, 2, 1.5456, 1.25)
       >>> var.extendVariable(extensionVar)
       >>> print extensionVar.allclose(answer, rtol = 1e-4)
       1

    Test case for a bug that occurs when initializing the distance
    variable at the interface. Currently it is assumed that adjacent cells
    that are opposite sign neighbors have perpendicular normal vectors. In
    fact the two closest cells could have opposite normals.

       >>> mesh = Grid1D(dx = 1., nx = 3)
       >>> var = DistanceVariable(mesh = mesh, value = (-1, 1, -1))
       >>> var.calcDistanceFunction()
       >>> print var.allclose((-0.5, 0.5, -0.5))
       1

    For future reference, the minimum distance for the interface cells can
    be calculated with the following functions. The trial cell values will
    also be calculated with these functions. In essence it is not
    difficult to calculate the level set distance function on an
    unstructured 3D grid. However a lot of testing will be required. The
    minimum distance functions will take the following form.

    .. raw:: latex

        $$ X_{\text{min}} = \frac{\left| \vec{s} \times \vec{t} \right|}
        {\left| \vec{s} - \vec{t} \right|} $$

        and in 3D,

        $$ X_{\text{min}} = \frac{1}{3!} \left| \vec{s} \cdot \left(
        \vec{t} \times \vec{u} \right) \right| $$

        where the vectors $\vec{s}$, $\vec{t}$ and $\vec{u}$ represent the
        vectors from the cell of interest to the neighboring cell.

    """
    def __init__(self, mesh, name = '', value = 0., unit = None, hasOld = 0, narrowBandWidth = 1e+10):
        """
        Creates a `distanceVariable` object.

        :Parameters:
          - `mesh`: The mesh that defines the geometry of this variable.
          - `name`: The name of the variable.
	  - `value`: The initial value.
	  - `unit`: the physical units of the variable
          - `hasOld`: Whether the variable maintains an old value.
          - `narrowBandWidth`: The width of the region about the zero level set
            within which the distance function is evaluated.

        """
        CellVariable.__init__(self, mesh, name = name, value = value, unit = unit, hasOld = hasOld)
        self._markStale()
        self.narrowBandWidth = narrowBandWidth

        self.cellToCellDistances = Numeric.array(MA.array(self.mesh._getCellToCellDistances()).filled(0))
        self.cellNormals = Numeric.array(MA.array(self.mesh._getCellNormals()).filled(0))       
        self.cellAreas = Numeric.array(MA.array(self.mesh._getCellAreas()).filled(0))
        self.cellToCellIDs = Numeric.array(self.mesh._getCellToCellIDsFilled())
        
    def _calcValue(self):
        return self.value
        
    def extendVariable(self, extensionVariable, deleteIslands = False):
        """
        
        Takes a `cellVariable` and extends the variable from the zero
        to the region encapuslated by the `narrowBandWidth`.

        :Parameters:
          - `extensionVariable`: The variable to extend from the zero
            level set.
          - `deleteIslands`: Sets the temporary level set value to
            zero in isolated cells.

        """
        
        self.tmpValue = self.value.copy()
        numericExtensionVariable = Numeric.array(extensionVariable)
        self._calcDistanceFunction(numericExtensionVariable, deleteIslands = deleteIslands)
        extensionVariable[:] = numericExtensionVariable
        self.value = self.tmpValue

    def calcDistanceFunction(self, narrowBandWidth = None, deleteIslands = False):
        """
        Calculates the `distanceVariable` as a distance function.

        :Parameters:
          - `narrowBandWidth`: The width of the region about the zero level set
            within which the distance function is evaluated.
          - `deleteIslands`: Sets the temporary level set value to
            zero in isolated cells.

        """
        self._calcDistanceFunction(narrowBandWidth = narrowBandWidth, deleteIslands = deleteIslands)
        self._markFresh()
    
    def _calcDistanceFunction(self, extensionVariable = None, narrowBandWidth = None, deleteIslands = False):

        if narrowBandWidth == None:
            narrowBandWidth = self.narrowBandWidth

        ## calculate interface values

        cellToCellIDs = self.mesh._getCellToCellIDs()

        if deleteIslands:
            adjVals = numerix.MAtake(self.value, cellToCellIDs)
            adjInterfaceValues = MA.masked_array(adjVals, mask = (adjVals * self.value[:,Numeric.NewAxis]) > 0)
            masksum = Numeric.sum(Numeric.logical_not(adjInterfaceValues.mask()), 1)
            tmp = MA.logical_and(masksum == 4, self.value > 0)
            self.value = MA.where(tmp, -1, self.value)

        adjVals = numerix.MAtake(self.value, cellToCellIDs)
        adjInterfaceValues = MA.masked_array(adjVals, mask = (adjVals * self.value[:,Numeric.NewAxis]) > 0)
        dAP = self.mesh._getCellToCellDistances()
        distances = abs(self.value[:,Numeric.NewAxis] * dAP / (self.value[:,Numeric.NewAxis] - adjInterfaceValues))
        indices = MA.argsort(distances, 1)
        sign = (self.value > 0) * 2 - 1

        index = Numeric.arange(len(indices[:,0])) * len(indices[0])

        s = MA.take(distances.flat, indices[:,0] + index)

        if self.mesh.getDim() == 2:

            t = MA.take(distances.flat, indices[:,1] + index)
            u = MA.take(distances.flat, indices[:,2] + index)

            ns = MA.take(MA.reshape(self.cellNormals.flat, (-1, 2)), indices[:,0] + index)
            nt = MA.take(MA.reshape(self.cellNormals.flat, (-1, 2)), indices[:,1] + index)

            signedDistance = MA.where(s.mask(),
                                      self.value,
                                      MA.where(t.mask(),
                                               sign * s,
                                               MA.where(abs(numerix.dot(ns,nt)) < 0.9,
                                                        sign * s * t / MA.sqrt(s**2 + t**2),
                                                        MA.where(u.mask(),
                                                                 sign * s,
                                                                 sign * s * u / MA.sqrt(s**2 + u**2)
                                                                 )
                                                        )
                                               )
                                      )
        else:
            signedDistance = MA.where(s.mask(),
                                      self.value,
                                      sign * s)
            

        self.value = signedDistance

        ## calculate interface flag
        masksum = Numeric.sum(Numeric.logical_not(distances.mask()), 1)
        interfaceFlag = masksum > 0

        ## spread the extensionVariable to the whole interface
        flag = True
        if extensionVariable is None:
            extensionVariable = Numeric.zeros(self.mesh.getNumberOfCells(), 'd')
            flag = False
            
        ext = Numeric.zeros(self.mesh.getNumberOfCells(), 'd')

        positiveInterfaceFlag = Numeric.where(self.value > 0, interfaceFlag, 0)
        negativeInterfaceIDs = Numeric.nonzero(Numeric.where(self.value < 0, interfaceFlag, 0))

        for id in negativeInterfaceIDs:
            tmp, extensionVariable[id] = self._calcTrialValue(id, positiveInterfaceFlag, extensionVariable)

        if flag:
            self.value = self.tmpValue.copy()

        ## evaluate the trialIDs
        adjInterfaceFlag = numerix.MAtake(interfaceFlag, cellToCellIDs)
        hasAdjInterface = Numeric.sum(adjInterfaceFlag.filled(), 1) > 0
        trialFlag = Numeric.logical_and(Numeric.logical_not(interfaceFlag), hasAdjInterface) 
        trialIDs = list(Numeric.nonzero(trialFlag))
        evaluatedFlag = interfaceFlag
        
        for id in trialIDs:
            self.value[id], extensionVariable[id] = self._calcTrialValue(id, evaluatedFlag, extensionVariable)

        while len(trialIDs):

            id = trialIDs[Numeric.argmin(abs(Numeric.take(self.value, trialIDs)))]
            trialIDs.remove(id)
            evaluatedFlag[id] = 1

            for adjID in cellToCellIDs[id].filled(fill_value = -1):
                if adjID != -1:
                    if not evaluatedFlag[adjID]:
                        self.value[adjID], extensionVariable[adjID] = self._calcTrialValue(adjID, evaluatedFlag, extensionVariable)
                        if adjID not in trialIDs:
                            trialIDs.append(adjID)

            if abs(self.value[id]) > narrowBandWidth / 2:
                break

        self.value = Numeric.array(self.value)

    def _calcTrialValue(self, id, evaluatedFlag, extensionVariable):
        adjIDs = self.cellToCellIDs[id]
        adjEvaluatedFlag = Numeric.take(evaluatedFlag, adjIDs)
        adjValues = Numeric.take(self.value, adjIDs)
        adjValues = Numeric.where(adjEvaluatedFlag, adjValues, 1e+10)
        indices = Numeric.argsort(abs(adjValues))
        sign = (self.value[id] > 0) * 2 - 1
        d0 = self.cellToCellDistances[id, indices[0]]
        v0 = self.value[adjIDs[indices[0]]]
        e0 = extensionVariable[adjIDs[indices[0]]]                             
        N = Numeric.sum(adjEvaluatedFlag)

        index0 = indices[0]
        index1 = indices[1]
        index2 = indices[self.mesh.getDim()]
        
        if N > 1:
            n0 = self.cellNormals[id, index0]
            n1 = self.cellNormals[id, index1]

            if self.mesh.getDim() == 2:
                cross = (n0[0] * n1[1] - n0[1] * n1[0])
            else:
                cross = 0.0
                
            if abs(cross) < 0.1:
                if N == 2:
                    N = 1
                elif N == 3:
                    index1 = index2
        if N == 0:
            raise Error 
        elif N == 1:
            return v0 + sign * d0, e0
        else:
            d1 = self.cellToCellDistances[id, index1]
            n0 = self.cellNormals[id, index0]
            n1 = self.cellNormals[id, index1]
            v1 = self.value[adjIDs[index1]]
            
            crossProd = d0 * d1 * (n0[0] * n1[1] - n0[1] * n1[0])
            dotProd = d0 * d1 * Numeric.dot(n0, n1)
            dsq = d0**2 + d1**2 - 2 * dotProd
            
            top = -v0 * (dotProd - d1**2) - v1 * (dotProd - d0**2)
            sqrt = crossProd**2 *(dsq - (v0 - v1)**2)
            sqrt = Numeric.sqrt(max(sqrt, 0))



            dis = (top + sign * sqrt) / dsq

            ## extension variable

            e1 = extensionVariable[adjIDs[index1]]
            a0 = self.cellAreas[id, index0]
            a1 = self.cellAreas[id, index1]

            if self.value[id] > 0:
                phi = max(dis, 0)
            else:
                phi = min(dis, 0)

            n0grad = a0 * abs(v0 - phi) / d0
            n1grad = a1 * abs(v1 - phi) / d1
            
            return dis, (e0 * n0grad + e1 * n1grad) / (n0grad + n1grad)

    def getCellInterfaceAreas(self):
        """
        Returns the length of the interface that crosses the cell

        A simple 1D test:

           >>> from fipy.meshes.grid1D import Grid1D
           >>> mesh = Grid1D(dx = 1., nx = 4)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-1.5, -0.5, 0.5, 1.5))
           >>> Numeric.allclose(distanceVariable.getCellInterfaceAreas(), 
           ...                  (0, 0., 1., 0))
           1

        A 2D test case:
        
           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = 1., dy = 1., nx = 3, ny = 3)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (1.5, 0.5, 1.5,
           ...                                              0.5,-0.5, 0.5,
           ...                                              1.5, 0.5, 1.5))
           >>> Numeric.allclose(distanceVariable.getCellInterfaceAreas(), 
           ...                  (0, 1, 0, 1, 0, 1, 0, 1, 0))
           1

        Another 2D test case:

           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> Numeric.allclose(distanceVariable.getCellInterfaceAreas(), 
           ...                  (0, Numeric.sqrt(2) / 4,  Numeric.sqrt(2) / 4, 0))
           1

        Test to check that the circumfrence of a circle is, in fact,
	
	.. raw:: latex
	
	   $2\pi r$.

	..
	
           >>> mesh = Grid2D(dx = 0.05, dy = 0.05, nx = 20, ny = 20)
           >>> r = 0.25
           >>> rad = Numeric.sqrt((mesh.getCellCenters()[:,0] - .5)**2 
           ...                    + (mesh.getCellCenters()[:,1] - .5)**2) - r
           >>> distanceVariable = DistanceVariable(mesh = mesh, value = rad)
           >>> print Numeric.sum(distanceVariable.getCellInterfaceAreas())
           1.57984690073
           
        """

        normals = Numeric.array(self._getCellInterfaceNormals().filled(fill_value = 0))
        areas = Numeric.array(self.mesh._getCellAreaProjections().filled(fill_value = 0))
        return Numeric.sum(abs(numerix.dot(normals, areas, axis = 2)), axis = 1)

    def _getCellInterfaceNormals(self):
        """
        
        Returns the interface normals over the cells.

           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> v = 1 / Numeric.sqrt(2)
           >>> answer = Numeric.array((((0, 0), (0, 0), (0, 0), (0, 0)), 
           ...                         ((0, 0), (0, 0), (0, 0), (v, v)),
           ...                         ((v, v), (0, 0), (0, 0), (0, 0)), 
           ...                         ((0, 0), (0, 0), (0, 0), (0, 0))))
           >>> Numeric.allclose(distanceVariable._getCellInterfaceNormals(), answer)
           1
           
        """

        N = self.mesh.getNumberOfCells()
        M = self.mesh._getMaxFacesPerCell()
        dim = self.mesh.getDim()

        valueOverFaces = Numeric.resize(Numeric.repeat(self._getCellValueOverFaces(), dim), (N, M, dim))

        interfaceNormals = numerix.MAtake(self._getInterfaceNormals(), self.mesh._getCellFaceIDs())
        import MA
        return MA.where(valueOverFaces < 0, 0, interfaceNormals)

    def _getInterfaceNormals(self):
        """

        Returns the normals on the boundary faces only, the other are set to zero.

           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> v = 1 / Numeric.sqrt(2)
           >>> answer = Numeric.array(((0, 0), (0, 0),
           ...                         (v, v), (0, 0),
           ...                         (0, 0), (0, 0),
           ...                         (0, 0), (v, v), (0, 0),
           ...                         (0, 0), (0, 0), (0, 0)))
           >>> Numeric.allclose(distanceVariable._getInterfaceNormals(), answer)
           1
           
        """
        
        N = self.mesh._getNumberOfFaces()
        M = self.mesh.getDim()
        interfaceFlag = Numeric.resize(Numeric.repeat(self._getInterfaceFlag(), M),(N, M))
        return Numeric.where(interfaceFlag, self._getLevelSetNormals(), 0)

    def _getInterfaceFlag(self):
        """

        Returns 1 for faces on boundary and 0 otherwise.

           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> answer = Numeric.array((0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0))
           >>> Numeric.allclose(distanceVariable._getInterfaceFlag(), answer)
           1
           
        """
        val0 = Numeric.take(Numeric.array(self.value), self.mesh._getAdjacentCellIDs()[0])
        val1 = Numeric.take(Numeric.array(self.value), self.mesh._getAdjacentCellIDs()[1])
        
        return Numeric.where(val1 * val0 < 0, 1, 0)

    def _getCellInterfaceFlag(self):
        """

        Returns 1 for those cells on the interface:

        >>> from fipy.meshes.grid2D import Grid2D
        >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
        >>> distanceVariable = DistanceVariable(mesh = mesh, 
        ...                                     value = (-0.5, 0.5, 0.5, 1.5))
        >>> answer = Numeric.array((0, 1, 1, 0))
        >>> Numeric.allclose(distanceVariable._getCellInterfaceFlag(), answer)
        1

        """

        flag = numerix.MAtake(self._getInterfaceFlag(), self.mesh._getCellFaceIDs()).filled(fill_value = 0)

        flag = Numeric.sum(flag, axis = 1)
        
        return Numeric.where(Numeric.logical_and(self.value > 0, flag > 0), 1, 0)

    def _getCellValueOverFaces(self):
        """

        Returns the cells values at the faces.

           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> answer = Numeric.array(((-.5, -.5, -.5, -.5),
           ...                         (.5, .5, .5, .5),
           ...                         (.5, .5, .5, .5),
           ...                         (1.5, 1.5, 1.5, 1.5)))
           >>> Numeric.allclose(distanceVariable._getCellValueOverFaces(), answer)
           1

        """
        
        M = self.mesh._getMaxFacesPerCell()
        N = self.mesh.getNumberOfCells()
        return Numeric.reshape(Numeric.repeat(Numeric.array(self.value), M), (N, M))

    def _getLevelSetNormals(self):
        """

        Return the face level set normals.

           >>> from fipy.meshes.grid2D import Grid2D
           >>> mesh = Grid2D(dx = .5, dy = .5, nx = 2, ny = 2)
           >>> distanceVariable = DistanceVariable(mesh = mesh, 
           ...                                     value = (-0.5, 0.5, 0.5, 1.5))
           >>> v = 1 / Numeric.sqrt(2)
           >>> answer = Numeric.array(((0, 0), (0, 0), (v, v), (v, v), (0, 0), (0, 0),
           ...                         (0, 0), (v, v), (0, 0), (0, 0), (v, v), (0, 0)))
           >>> Numeric.allclose(distanceVariable._getLevelSetNormals(), answer)
           1
        """
        
        faceGrad = self.getGrad().getArithmeticFaceValue()
        faceGradMag = Numeric.array(faceGrad.getMag())
        faceGradMag = Numeric.where(faceGradMag > 1e-10,
                                    faceGradMag,
                                    1e-10)
        faceGrad = Numeric.array(faceGrad)

        ## set faceGrad zero on exteriorFaces
        dim = self.mesh.getDim()
        exteriorFaces = (self.mesh.getExteriorFaceIDs() * dim)[:,Numeric.NewAxis] + Numeric.resize(Numeric.arange(dim), (len(self.mesh.getExteriorFaces()),dim))
        Numeric.put(faceGrad, exteriorFaces, Numeric.zeros(exteriorFaces.shape,'d'))
        
        return faceGrad / faceGradMag[:,Numeric.NewAxis] 

def _test(): 
    import doctest
    return doctest.testmod()
    
if __name__ == "__main__": 
    _test()         
    



            
            
        
                
