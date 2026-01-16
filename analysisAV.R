# Analysis of action verbs in SOM learning objectives, grouped by module, discipline
# Stephan Bandelow, May 2024


# load data
library(RSQLite)
conn = dbConnect(RSQLite::SQLite(), "semantics.db")

# retrieve grouping data from objectives with action verb data from AVmap
s = "SELECT objectives.course, objectives.module, objectives.discipline, objectives.lecture, objectives.title, AVmap.sentence, AVmap.verb, AVmap.bloom FROM objectives LEFT JOIN AVmap ON objectives.id = AVmap.objid ORDER BY objectives.id, AVmap.sentence"
res = dbSendQuery(conn, s)
avdat = dbFetch(res)
dbClearResult(res)
dbDisconnect(conn)
flt = !is.na(avdat$bloom)
str(avdat)

# summary stats (mean, sd, 95% CI) by grouping variable
summaryByFactor = function (x, grp, grp.label = 'group') {
    mn = tapply(x, grp, mean)
    sdv = tapply(x, grp, sd)
    n = tapply(x, grp, length)
    ci95 = qnorm(0.975) * sdv / sqrt(n)
    lbl = names(n)
    sdat = data.frame(lbl, mn, sdv, ci95, n)
    names(sdat) = c(grp.label, 'mean', 'sd', 'ci95', 'n')
    return(sdat)
}

# plots
library(ggplot2)
library(gridExtra)

pdf("LO_actionVerbs.pdf", paper = 'A4')

# overall Bloom level distribution
hist(avdat$bloom, breaks = 20, main = 'Bloom level distribution of all action verbs\n6189 identified in 6612 sentences from 6483 objectives')
# raw verb frequencies
frq = tapply(avdat$verb[flt], avdat$verb[flt], length)
frq = frq[order(frq, decreasing = TRUE)]
barplot(frq[1:10], main = "Frequency of top 10 action verbs\ntotal = 6189", cex.names = 0.5)

# averages by course, module, discipline
courses = summaryByFactor(avdat$bloom[flt], avdat$course[flt], grp.label = 'course')
moduleorder = unique(avdat$module)
avdat$module = ordered(avdat$module, levels = moduleorder) # order modules by delivery temporal progression
modules = summaryByFactor(avdat$bloom[flt], avdat$module[flt], grp.label = 'module')
disciplines = summaryByFactor(avdat$bloom[flt], avdat$discipline[flt], grp.label = 'discipline')

ylbl = expression(paste('mean ' %+-% ' 95% CI'))
ggplot(courses, aes(x = course, y = mean)) +
    geom_errorbar(aes(ymin = mean - ci95, ymax = mean + ci95)) +
    geom_point() +
    ggtitle('Action verb Bloom levels by Course') +
    ylab(ylbl)
ggplot(modules, aes(x = factor(module, level = moduleorder), y = mean)) +
    geom_errorbar(aes(ymin = mean - ci95, ymax = mean + ci95)) +
    geom_point() +
    ggtitle('Action verb Bloom levels by Module') +
    ylab(ylbl) +
    xlab('module (in delivery order)')


ggplot(disciplines, aes(x = discipline, y = mean)) +
    geom_errorbar(aes(ymin = mean - ci95, ymax = mean + ci95)) +
    geom_point() +
    ggtitle('Action verb Bloom levels by Discipline') +
    ylab(ylbl) +
    theme(axis.text.x = element_text(size = 6))

# grid.arrange(p2, p3, p4, ncol = 2)  # show all subplots in 1 larger plot

dev.off()
