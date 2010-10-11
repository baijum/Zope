##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from itertools import chain, combinations

_marker = []

class PermuteKeywordList:
    """
        returns a flat list of a sequential
        permutation of keyword lists.
        Example:

        A = [[1,2,3],[4,5],[6,7]]

        tree permutation
 
               6
              / 
             4
            / \
           /   7
          1   
           \   6
            \ /
             5
              \
               7
 
               6
              / 
             4
            / \
           /   7
          2   
           \   6
            \ /
             5
              \
               7
          
               6
              / 
             4
            / \
           /   7
          3   
           \   6
            \ /
             5
              \
               7

     
     corresponds to following flat list

         [[1,4,6],[1,4,7],[1,5,6],[1,5,7],
          [2,4,6],[2,4,7],[2,5,6],[2,5,7],
          [3,4,6],[3,4,7],[3,5,6],[3,5,7]]


    """

    
    
    def __init__(self,A):
        """ A -- list of keyword lists"""
        self.keys=[]
        self.walking(A)
        

    def walking(self,A,f=_marker):

        if f is _marker:
            f = []

        if A[:1]:
            first = A[0]
            for l in first:
                next = f[:] + [l]
                self.walking(A[1:],next)
            
        else:
            self.keys.append(tuple(f))




def powerset(iterable,start=0):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(start,len(s)+1))
