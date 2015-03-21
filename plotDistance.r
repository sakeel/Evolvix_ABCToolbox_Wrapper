#
#  @file  plotDistance.r
#
#  Licensing of this file is governed by the Evolvix Contributors License Agreement
#  as described at http://evolvix.org/intro/legal
#
#  The license chosen for this file is the BSD-3-Clause
#  ( http://opensource.org/licenses/BSD-3-Clause ):
#
#  Copyright (c) 7/11/13  Authors and contributors as listed in the corresponding
#                code repository of this file and associated organizations if applicable.
#                All rights reserved.
#/////////////////////////////////////////////////////////////////////////////
#  Redistribution and use in source and binary forms, with or without modification,
#  are permitted provided that the following conditions are met:
#   - Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   - Neither the names of authors nor the names of their organizations nor
#     the names of other contributors to the project may be used to endorse or promote
#     products derived from this software without specific prior written permission.
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
#  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
#  OF THE POSSIBILITY OF SUCH DAMAGE.
#/////////////////////////////////////////////////////////////////////////////

library(akima)
library(rgl)
#questName<-commandArgs()[length(commandArgs())];
#if(length(commandArgs()) < 7) {
#    stop("Provide a quest name as an argument.");
#}

questName = "birthDeath"

plotDistances = function(distanceFunctionName) {
    dataPath = paste("../quests/", questName, "/results/", distanceFunctionName, ".txt", sep="")
    data = read.table(dataPath, header=TRUE)
    interpData = interp(log10(data$birthRate), log10(data$deathRate), log10(data$myDist), duplicate="mean", extrap=FALSE, linear=TRUE)

    zData = interpData$z
    zData[is.na(zData)] = 0
    translatedZData = zData - min(zData, na.rm=TRUE)
    normalizedZData = translatedZData / max(translatedZData, na.rm=TRUE)

    open3d()
    surface3d(interpData$x, interpData$y, interpData$z, col=rgb(1-normalizedZData, 0, normalizedZData), main=distanceFunctionName)
    axes3d()
}

for(name in c("L2", "normalized_L2", "geometric")) {
    plotDistances(name)
}
