package declmath

import java.io.File
import javax.xml.parsers.SAXParserFactory

import scala.xml.{Elem, Source, XML}

/**
  * Created by unruh on 5/21/17.
  */
class Document(xml: Elem) {
  def formulas = for (x <- xml \\ "math") yield CMathML.fromPMML(x)
}

object Document {
  def load(file : File) : Document = {
    val fact = SAXParserFactory.newInstance()
    fact.setValidating(false)
    fact.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false)
    val source = Source.fromFile(file)
    val parser = fact.newSAXParser()
    val xml = XML.loadXML(source,parser)
    new Document(xml)
  }
  def load(file : String) : Document = load(new File(file))

  def main(args: Array[String]): Unit = {
    val doc = Document.load("/home/unruh/svn/queasycrypt/trunk/declmath/test.xhtml")
    for (f <- doc.formulas) {
      println("=========== "+f)
      val (env, cons, typ, vars) = f.getTypeConstraints(Consts.consts)
      println(typ)
      println(env.toTypeEnv)
      println(cons.toTypeCostraints)
      cons.inference(env)
      println(env.toTypeEnv)
      for ((v,t) <- vars) { println(v+" : "+env.get(t)); }
    }
  }
}
