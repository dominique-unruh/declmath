package declmath

import scala.collection.immutable.HashMap

/**
  * Created by unruh on 5/21/17.
  */
object Consts {
  import Type._
  private def mapConsts(consts: ((String,Type),Seq[Constraint])*) : Map[(String,String),(Type,List[Constraint])] =
    (consts map { case ((c,t),cs) => (CSymbol.split(c),(t,cs.toList)) }).toMap
  private def tc(tcs : (String,String)*) : Seq[Constraint] = tcs map {
    case (x,y) => SortConstraint(TVar(x),Sort(List(y)))
  }

  val consts : Map[(String,String),(Type,List[Constraint])] = mapConsts(
    "arith1.abs" -> fun(real,real) -> Nil,
    "arith1.plus" -> fun(TVar("n"),TVar("n"),TVar("n")) -> tc("n"->"number"),
    "fns1.left_compose" -> fun(fun(TVar("b"),TVar("c")),fun(TVar("a"),TVar("b")),fun(TVar("a"),TVar("c"))) -> Nil,
    "local.apply" -> fun(fun(TVar("x"),TVar("y")),TVar("x"),TVar("y")) -> Nil
  )
}
